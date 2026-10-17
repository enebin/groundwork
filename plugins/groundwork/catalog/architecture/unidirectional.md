# unidirectional

Token cost levels are relative estimates within this step, not measurements.

Summary: Each screen has a pure reducer that turns `(State, Input)` into a `Decision` (next state plus effects to run), and a screen-specific store that owns the state, saves the decision, and runs the effects. Effect completions come back as new inputs. State changes in exactly one place.

```
View ─▶ store.send(Input) ─▶ reducer.reduce(state, input) ─▶ Decision
                                   ┌────────────────────────────┘
                                   ├─ state = decision.nextState      observed → View redraws
                                   └─ run(effect) …                   I/O, start tasks
                                        └─ completion ─▶ store.send(completion Input) ─▶ …
```

Typical stack: Swift / SwiftUI with `@Observable`. The same shape works with React `useReducer` plus effect hooks, or Kotlin flows.

Fits:
- Screens with many asynchronous transitions: loading, paging, refresh, live updates, cancellation, late responses.
- Code where you want every transition tested without I/O.
- Teams that have been bitten by state changed from several places.

Does not fit:
- Screens with one or two simple values (a toggle, a text field). A plain observable value is enough.
- Prototypes where screens change daily; each new async behavior costs several edits.

## Example (Swift)

```swift
nonisolated struct Decision<State, Effect>: Equatable, Sendable
where State: Equatable & Sendable, Effect: Equatable & Sendable {
    var nextState: State
    var effects: [Effect] = []
}

nonisolated struct ItemListState: Equatable, Sendable {
    enum Phase: Equatable, Sendable { case idle, loading, loaded([Item]), failed(String) }
    var phase: Phase = .idle
}

nonisolated enum ItemListInput: Equatable, Sendable {
    case appeared
    case loadFinished([Item])
    case loadFailed(String)
}

nonisolated enum ItemListEffect: Equatable, Sendable { case load }

nonisolated struct ItemListReducer {
    func reduce(_ state: ItemListState, _ input: ItemListInput) -> Decision<ItemListState, ItemListEffect> {
        switch (state.phase, input) {
        case (.loading, .appeared):
            return Decision(nextState: state)
        case (_, .appeared):
            return Decision(nextState: .init(phase: .loading), effects: [.load])
        case (.loading, .loadFinished(let items)):
            return Decision(nextState: .init(phase: .loaded(items)))
        case (.loading, .loadFailed(let message)):
            return Decision(nextState: .init(phase: .failed(message)))
        case (_, .loadFinished), (_, .loadFailed):
            return Decision(nextState: state)
        }
    }
}

@MainActor @Observable
final class ItemListStore {
    private(set) var state = ItemListState()
    private let reducer = ItemListReducer()
    private let repository: any ItemRepository
    private var loadTask: Task<Void, Never>?

    init(repository: any ItemRepository) { self.repository = repository }

    func send(_ input: ItemListInput) {
        let decision = reducer.reduce(state, input)
        state = decision.nextState
        decision.effects.forEach(run)
    }

    private func run(_ effect: ItemListEffect) {
        switch effect {
        case .load:
            loadTask?.cancel()
            loadTask = Task {
                let input: ItemListInput
                do { input = .loadFinished(try await repository.items()) }
                catch { input = .loadFailed(error.localizedDescription) }
                guard !Task.isCancelled else { return }
                send(input)
            }
        }
    }
}
```

The reducer test needs no doubles: build a state, send an input, compare the decision. The store test injects a repository double and checks effect order, task replacement, and that a cancelled task's completion is dropped.

Pros:
- Every transition is testable as a pure function: no `await`, no doubles, no real time.
- State changes in one place, so "who set this?" has one answer.
- Ignored inputs are explicit, so a late completion cannot silently overwrite newer state.
- Late-result handling lives in one spot (the store checks cancellation right before sending the completion).

Cons:
- Adding one async behavior touches five places: the intent input, the effect, the store's run branch, the completion input, and the reduce branch.
- More types per screen (state, input, effect, reducer, store) than a view model.
- Errors must become equatable values (for example a display string) before they enter an input, so the reducer test can compare decisions.
- The benefit only arrives if reducer tests are actually written; without them it is all cost.

Token cost: High — one new async behavior touches five places plus reducer and store tests, and the reviewer reads all of them.

Recommended when: screens have several overlapping async flows and you will write reducer tests for every input.

## Failure modes to avoid

These come from a codebase that adopted this pattern, reverted it, and adopted it again with the fixes below.

- **No generic store.** A `Store<R: Reducer>` saves nothing: the run side (task slots, streams, waiting) differs per screen. Each screen gets a concrete store.
- **The reducer holds no dependencies.** A reducer that holds a repository or task bag and runs effects itself is not pure, and its tests must go through `await`. Only the store runs effects.
- **Transitions live in one place.** Do not split one transition between a mutating method on the state and a reduce branch. Private helpers inside the reducer for readability are fine.
- **No shared reducer protocol until a caller needs it.** With concrete stores, nothing calls a reducer through a protocol, so the protocol enforces nothing. Share only what is truly repeated (the `Decision` type). Add a protocol when generic code needs to call reducers.
- **Split a reducer by lifetime, not by length.** When two independent lifetimes (for example a list and an upload) mix in one reducer and state combinations keep multiplying, split it. If one flag forces you to multiply state cases, the model is wrong.

## Contract to write

````markdown
## State and data flow

Screen state uses a unidirectional reducer pattern. Each screen has three parts.

| Part | Shape | Job |
|---|---|---|
| Reducer | value type, no stored state | `(State, Input) -> Decision`. A synchronous pure function that decides the next state and the effects to run |
| State | value type, equatable | The values transitions depend on |
| Store | observable reference type, one per screen | Owns the state. Receives inputs, calls the reducer, saves the decision, runs the effects |

```
View ─▶ store.send(Input) ─▶ reducer.reduce(state, input) ─▶ Decision
                                   ├─ state = decision.nextState
                                   └─ run(effect) ─▶ completion ─▶ store.send(completion Input)
```

### Contract

- The reducer stores nothing and does no I/O. It does not know async, throwing, repositories, tasks, or the clock. The same `(State, Input)` always gives the same `Decision`.
- `Decision` is `nextState` plus `effects`. An ignored input still returns `Decision(nextState: state)`. Do not return nil or use a broad default case to skip inputs.
- State changes in one place only: where the store saves `nextState`. Effect completions never change state directly; they send a new input.
- The store saves the next state before any await, and runs effects in the order they were declared.
- The reducer takes only configuration that never changes after creation. Anything that can change goes through state or input.
- State, input, effect, and decision are equatable and safe to send across concurrency domains. Convert errors to display values before they enter an input.
- The store runs each effect in a named task slot. A new task in a slot cancels the previous one. Before sending a completion input, the store checks that its task was not cancelled. Do not add generation counters for this.
- Views read the store's state and call `send`. Views and rows display only.
- No generic store type and no shared reducer protocol. Share the `Decision` type only. Add a protocol when generic code needs to call reducers.
- Simple screens with one or two independent values may use a plain observable value instead. Say so in that screen's section.

### Tests

- Reducer tests build state and input directly and compare decisions. No store, no doubles, no await. For every input, test the normal path, the ignored case, the failure, and a late completion.
- Store tests cover only what the reducer cannot see: effect execution and order, state saved before await, task replacement, dropping late completions, stream consumption. Inject repository doubles through the constructor.
- If a transition cannot be tested without the store, decision or I/O has leaked into the wrong layer.
````

## Review checklist

- The reducer has no stored properties, no async, no throws, no I/O, no clock or randomness.
- Every input is handled by an explicit branch; no broad `default` or nil return that hides an input.
- State is assigned only where the store saves `nextState`. No effect completion writes state directly.
- The store checks cancellation (or the current state case) right before sending a completion input; no generation counter.
- No generic `Store<R>` and no shared reducer protocol introduced without a generic caller.
- A transition is not split between a state mutating method and a reduce branch.
- New inputs come with reducer tests for normal, ignored, failure, and late-completion cases; store behavior changes come with store tests.
- Views do not hold transition logic or call I/O.
