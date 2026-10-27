"""Separate processes share only temporary files and fake service responses."""
import contextlib
import importlib.util
import json
import multiprocessing
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

SKILL = Path(__file__).resolve().parents[1] / "plugins/groundwork/skills/slack-report"
TIMEOUT = 10
REPOSITORY = "T_TEST-example-work"
CHANNEL = "C_TEST"
TITLE = "Saved filters are ready"
BODY = "Tests passed."
ALPHA = "step/alpha"
BETA = "step/beta"


def report_worker(directory, branch, operation, role, connection):
    spec = importlib.util.spec_from_file_location("concurrent_post", SKILL / "post.py")
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    root = Path(directory)
    original_load = helper.load_threads
    if os.name == "nt":
        import msvcrt as locking_module
        lock_name = "locking"
        exclusive = locking_module.LK_LOCK
        nonblocking = locking_module.LK_NBLCK
    else:
        import fcntl as locking_module
        lock_name = "flock"
        exclusive = locking_module.LOCK_EX
        nonblocking = exclusive | locking_module.LOCK_NB
    original_lock = getattr(locking_module, lock_name)

    def wait_for_release():
        if not connection.poll(TIMEOUT):
            raise TimeoutError("The test did not release the worker")
        if connection.recv() != "release":
            raise AssertionError("Unexpected worker command")

    def load_threads(repo):
        result = original_load(repo)
        if role == "second":
            connection.send("loaded")
            wait_for_release()
        return result

    def lock(file, flags, *extra):
        if role == "second" and flags == exclusive:
            try:
                original_lock(file, nonblocking, *extra)
                return
            except OSError:
                connection.send("waiting")
        original_lock(file, flags, *extra)

    def current_pr(*args):
        if role == "first":
            connection.send("ready")
            wait_for_release()
        return None

    def fake_post(token, channel, text, thread_ts=None):
        if operation == "fail":
            raise RuntimeError("Fake parent creation failed")
        if thread_ts is None:
            with (root / "parents").open("a") as output:
                output.write(branch + "\n")
        return {"channel": CHANNEL, "ts": branch}

    try:
        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.object(helper, "THREADS_DIR", root / "threads"))
            stack.enter_context(patch.object(helper, "load_threads", side_effect=load_threads))
            stack.enter_context(patch.object(helper, "current_pr", side_effect=current_pr))
            stack.enter_context(patch.object(helper, "post", side_effect=fake_post))
            stack.enter_context(patch.object(helper, "invite_owner"))
            stack.enter_context(patch.object(locking_module, lock_name, side_effect=lock))
            if operation == "sync":
                helper.sync_other_threads("fake-token", REPOSITORY, None)
            elif operation == "fail":
                try:
                    helper.post_branch_report("fake-token", CHANNEL, REPOSITORY, branch, TITLE, BODY)
                except RuntimeError:
                    pass
                else:
                    raise AssertionError("Parent creation should have failed")
            else:
                helper.post_branch_report("fake-token", CHANNEL, REPOSITORY, branch, TITLE, BODY)
        connection.send("done")
    except BaseException as error:
        connection.send(("error", repr(error)))
        raise
    finally:
        connection.close()


class ConcurrentReportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.context = multiprocessing.get_context("spawn")
        self.processes = []
        self.connections = []
        self.addCleanup(self.stop_workers)
        spec = importlib.util.spec_from_file_location("concurrency_parent", SKILL / "post.py")
        self.helper = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.helper)
        self.helper.THREADS_DIR = self.root / "threads"
        self.helper.THREADS_DIR.mkdir()

    def stop_workers(self):
        for process in self.processes:
            if process.is_alive():
                process.terminate()
            process.join(TIMEOUT)
        for connection in self.connections:
            connection.close()

    def start_worker(self, branch, operation, role):
        parent, child = self.context.Pipe()
        process = self.context.Process(target=report_worker, args=(str(self.root), branch, operation, role, child))
        self.processes.append(process)
        self.connections.append(parent)
        process.start()
        child.close()
        return parent, process

    def receive(self, connection):
        self.assertTrue(connection.poll(TIMEOUT), "Worker did not reach its next bounded checkpoint")
        message = connection.recv()
        self.assertNotIsInstance(message, tuple, f"Worker failed: {message}")
        return message

    def finish(self, connection, process):
        self.assertEqual(self.receive(connection), "done")
        process.join(TIMEOUT)
        self.assertFalse(process.is_alive(), "Worker did not exit")
        self.assertEqual(process.exitcode, 0)

    def overlap_reports(self, second_branch):
        first, first_process = self.start_worker(ALPHA, "report", "first")
        self.assertEqual(self.receive(first), "ready")
        second, second_process = self.start_worker(second_branch, "report", "second")
        checkpoint = self.receive(second)
        self.assertIn(checkpoint, ("waiting", "loaded"))
        first.send("release")
        self.finish(first, first_process)
        if checkpoint == "waiting":
            self.assertEqual(self.receive(second), "loaded")
        second.send("release")
        self.finish(second, second_process)
        return self.helper.load_threads(REPOSITORY)[1]

    def test_concurrent_branches_keep_both_saved_threads(self):
        # Given two processes reporting different branches to one channel.
        # When the second starts while the first is creating its parent.
        threads = self.overlap_reports(BETA)
        # Then neither branch loses its saved parent.
        self.assertEqual(set(threads), {ALPHA, BETA})
        self.assertEqual(threads[ALPHA]["ts"], ALPHA)
        self.assertEqual(threads[BETA]["ts"], BETA)

    def test_concurrent_reports_on_one_branch_create_one_parent(self):
        # Given two processes reporting the same branch to one channel.
        # When their parent lookup overlaps.
        threads = self.overlap_reports(ALPHA)
        # Then both reports reuse one saved parent.
        self.assertEqual(set(threads), {ALPHA})
        self.assertEqual((self.root / "parents").read_text().splitlines(), [ALPHA])

    def test_late_status_refresh_preserves_a_new_branch_thread(self):
        # Given a saved branch whose status refresh is paused after reading.
        path, _ = self.helper.load_threads(REPOSITORY)
        path.write_text(json.dumps({ALPHA: {"channel": CHANNEL, "ts": ALPHA, "title": TITLE}}))
        first, first_process = self.start_worker(ALPHA, "sync", "first")
        self.assertEqual(self.receive(first), "ready")
        # When another process saves a new branch during that refresh.
        second, second_process = self.start_worker(BETA, "report", "second")
        checkpoint = self.receive(second)
        self.assertIn(checkpoint, ("waiting", "loaded"))
        if checkpoint == "waiting":
            first.send("release")
            self.finish(first, first_process)
            self.assertEqual(self.receive(second), "loaded")
        second.send("release")
        self.finish(second, second_process)
        if checkpoint == "loaded":
            first.send("release")
            self.finish(first, first_process)
        # Then the late refresh cannot erase the new branch.
        threads = self.helper.load_threads(REPOSITORY)[1]
        self.assertEqual(set(threads), {ALPHA, BETA})

    def test_failed_parent_creation_releases_the_lock_for_another_process(self):
        # Given a process whose parent message fails inside the lock.
        failed, failed_process = self.start_worker(ALPHA, "fail", "unblocked")
        self.finish(failed, failed_process)
        # When another process reports to the same channel.
        next_report, next_process = self.start_worker(BETA, "report", "unblocked")
        self.finish(next_report, next_process)
        # Then the failed attempt saved nothing and left no held lock.
        threads = self.helper.load_threads(REPOSITORY)[1]
        self.assertEqual(set(threads), {BETA})
        self.assertEqual((self.root / "parents").read_text().splitlines(), [BETA])

    def test_windows_lock_releases_its_byte_when_the_operation_fails(self):
        # Given the Windows locking boundary and a failed operation.
        windows = SimpleNamespace(LK_LOCK=1, LK_UNLCK=2, locking=Mock())
        platform = SimpleNamespace(name="nt", SEEK_END=os.SEEK_END)
        failure = "Failed while holding the lock"
        # When an exception leaves the protected operation.
        with patch.object(self.helper, "os", platform), patch.dict(sys.modules, {"msvcrt": windows}):
            with self.assertRaisesRegex(RuntimeError, failure):
                with self.helper.thread_lock(REPOSITORY):
                    raise RuntimeError(failure)
        # Then the same first byte was locked and unlocked.
        calls = windows.locking.call_args_list
        self.assertEqual(len(calls), 2)
        descriptor = calls[0].args[0]
        self.assertEqual(calls[0].args, (descriptor, windows.LK_LOCK, 1))
        self.assertEqual(calls[1].args, (descriptor, windows.LK_UNLCK, 1))
        self.assertEqual(next(self.helper.THREADS_DIR.glob("*.lock")).read_bytes(), b"\0")
