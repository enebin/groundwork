# mvvm

Token cost levels are relative estimates within this step, not measurements.

Summary: Each screen has an observable view model that owns the screen's state and exposes methods the view calls. The view model talks to injected repositories and updates its own state. Views display state and forward user actions.

```
View ─▶ viewModel.load() / viewModel.select(id) ─▶ ViewModel
                                                     ├─ state = .loading           observed → View redraws
                                                     └─ await repository.items()
                                                          └─ state = .loaded(items)   (after checking it is still current)
```

Typical stack: Swift / SwiftUI with `@Observable`. Also common with Kotlin + Jetpack ViewModel.

Fits:
- Screens with moderate state and a few async calls.
- Teams that already know MVVM and want the least new vocabulary.
- Apps where most screens are forms, lists, and detail views.

Does not fit:
- Screens with many overlapping async flows (paging + refresh + live stream + cancellation). Transitions spread across methods and become hard to test. Consider `unidirectional`.
- Teams that want every transition tested without async doubles.

## Example (Swift)

```swift
@MainActor @Observable
final class ItemListViewModel {
    enum Phase: Equatable { case idle, loading, loaded([Item]), failed(String) }

    private(set) var phase: Phase = .idle
    private let repository: any ItemRepository
    private var loadTask: Task<Void, Never>?

    init(repository: any ItemRepository) { self.repository = repository }

    func load() {
        guard phase != .loading else { return }
        phase = .loading
        loadTask?.cancel()
        loadTask = Task {
            let result: Phase
            do { result = .loaded(try await repository.items()) }
            catch { result = .failed(error.localizedDescription) }
            guard !Task.isCancelled, phase == .loading else { return }
            phase = result
        }
    }
}

struct ItemListView: View {
    @State private var viewModel: ItemListViewModel

    init(repository: any ItemRepository) {
        _viewModel = State(initialValue: ItemListViewModel(repository: repository))
    }

    var body: some View {
        content.task { viewModel.load() }
    }
}
```

Tests inject a repository double, call a method, await or poll for the state, and assert.

Pros:
- Fewest types per screen; one class to read.
- Familiar to most mobile developers; little onboarding.
- Adding one async behavior is one method, often one edit.

Cons:
- Transitions are spread across methods; "what can change `phase`?" means reading the whole class.
- Every transition test needs a repository double and async waiting, so tests are slower and fewer get written.
- Late completions must be guarded in every method that awaits; it is easy to forget one.
- View models tend to grow into the place where everything goes (formatting, navigation, I/O, rules).

Token cost: Low — most changes are one method in one class; the reviewer reads that class and its tests.

Recommended when: screens are mostly forms, lists, and details with a few async calls, and the team knows MVVM.

## Failure modes to avoid

- **No base view model class or generic view model.** Shared behavior goes into small helpers called explicitly, not into inheritance.
- **One owner per state.** Only the view model writes its state. Views and child components send actions; they do not mutate shared state.
- **Guard before writing after an await.** Check cancellation and the current state case right before assigning a result. Do not add generation counters.
- **Keep pure logic out of the view model.** Formatting, filtering, and validation go into pure functions that are tested without the view model.
- **Do not let the view create its own I/O.** The view model receives repositories through its initializer; the view never builds one.
- **Recreate the view model when its identity changes.** A view model stored in view state keeps its first value; key the view by the inputs that define it (for example the item id or the backend instance).

## Contract to write

````markdown
## State and data flow

Each screen has one observable view model. It owns the screen's state, exposes intent methods, and calls injected repositories.

```
View ─▶ viewModel.intent() ─▶ state = loading ─▶ await repository ─▶ check still current ─▶ state = result
```

### Contract

- The view model is the only writer of its state. Views read state and call intent methods. Views and rows display only.
- The view model receives its repositories and other dependencies through its initializer. It never creates them.
- After every await, check cancellation and the current state right before writing the result. Do not add generation or epoch counters.
- Each long-running job has one task slot. Starting a new job in the slot cancels the old one.
- Formatting, filtering, validation, and other pure rules live in pure functions or small value types, not in the view model.
- No base view model class, no generic view model, no shared view model protocol without a generic caller.
- The view owns the view model in its own state storage and keys the view by the inputs that define the view model, so a changed input creates a new view model.
- When a screen's transitions grow so that one method's change breaks another's assumptions, record it here and consider a reducer for that screen.

### Tests

- View model tests inject repository doubles through the initializer, call intent methods, and assert state. Test the normal path, the failure, a repeated call while busy, and a late completion after cancellation.
- Pure rules are tested directly, without the view model.
- Wait for async state with a bounded polling helper, never with sleeps.
````

## Review checklist

- State is written only inside the view model; views do not mutate it.
- Dependencies arrive through the initializer; no view model reaches for a global or builds its own repository.
- Every assignment after an await is guarded by a cancellation and current-state check; no generation counter.
- Pure logic added to the view model is moved to a pure function when it can be tested alone.
- No base class, generic view model, or protocol introduced without a second implementation or caller.
- The view keys or recreates the view model when its defining input changes.
- New intent methods come with tests for normal, failure, repeated, and late-completion cases.
