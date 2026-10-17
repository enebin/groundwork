# layered-web

Token cost levels are relative estimates within this step, not measurements.

Summary: A web frontend in three layers with one-way dependencies: Presentation (pages and components) → Domain (types, pure rules, domain hooks) → Data (API client and query hooks). Components never call the API directly. Pages only compose.

```
pages/            ─▶ hooks/domain/, lib/utils/, types/ ─▶ hooks/queries/ ─▶ lib/network/
components/            pure rules, domain types             React Query        HTTP only
[Presentation]         [Domain]                             [Data → Domain]    [Data]
```

Typical stack: React + TypeScript + React Query. The layering also fits Vue + TanStack Query or Svelte with stores.

Fits:
- Single-page apps backed by an HTTP API, with real business rules on the client (availability, validation, formatting).
- Codebases where components have started calling `fetch` and holding rules.

Does not fit:
- Static or content sites with little client logic.
- Server-component-first apps where data loading lives on the server; the Data layer looks different there.

## Example (TypeScript, React)

```tsx
// lib/network/api.ts — [Data]
export const api = {
  products: (): Promise<Product[]> => http.get("/products"),
};

// hooks/queries/useProducts.ts — [Data → Domain]
export function useProducts() {
  return useQuery({ queryKey: ["products"], queryFn: api.products });
}

// lib/utils/productAvailability.ts — [Domain], pure
export function availableProducts(products: Product[], now: Date): Product[] {
  return products.filter((product) => product.active && product.stock > 0 && isOnSale(product, now));
}

// hooks/domain/useAvailableProducts.ts — [Domain]
export function useAvailableProducts(now: Date) {
  const { data = [], ...rest } = useProducts();
  return { products: availableProducts(data, now), ...rest };
}

// components/ProductList.tsx — [Presentation], props only
export function ProductList({ products, onSelect }: { products: Product[]; onSelect: (id: number) => void }) {
  return <ul>{products.map((product) => <li key={product.id} onClick={() => onSelect(product.id)}>{product.name}</li>)}</ul>;
}

// pages/ProductsPage.tsx — [Presentation], composition only
export function ProductsPage() {
  const now = useNow();
  const { products, isLoading } = useAvailableProducts(now);
  const navigate = useNavigate();
  if (isLoading) return <Spinner />;
  return <ProductList products={products} onSelect={(id) => navigate(`/products/${id}`)} />;
}
```

`availableProducts` is tested as a plain function. `ProductList` is tested with props. Only the query hook touches the network.

For complex state with clear inputs and outputs (measuring, timers, subscriptions), split a pure reducer in `lib/utils/` from a hook whose effects do the outside work and only dispatch events. Simple state (an input value, open/closed) stays in `useState`.

Pros:
- Rules are pure functions, tested without a DOM or network.
- Components are reusable because they only take props.
- Caching, refetching, and loading states live in one place (the query hooks).
- Each layer has an obvious folder, so new code has an obvious home.

Cons:
- Small features touch four or five files across folders.
- The domain hook vs pure util line needs judgment.
- Migrating an existing app is gradual; old components that fetch directly coexist with new ones.
- Query keys and invalidation must be kept consistent by hand.

Token cost: Medium — a feature touches four or five files across layer folders; each is small and easy to review.

Recommended when: the project is a single-page app over an HTTP API with real rules on the client.

## Failure modes to avoid

- **API calls in components.** A single `api.x()` in a component bypasses caching and makes it untestable without the network.
- **Pages with logic.** Filtering, validation, and formatting inside a page cannot be tested or reused.
- **Shared components that fetch.** A shared component that gains page-specific state or a network call can no longer be shared.
- **Copies of shared rules and API types.** One source per rule and per API type; do not let a frontend copy drift from the backend's definition without a check.
- **Reducers for trivial state.** A reducer for one boolean is more code, not more clarity.
- **Hard-coded design values.** Colors, spacing, and font sizes come from tokens; add the token first.

## Contract to write

````markdown
## Frontend layers

The frontend has three layers. Dependencies point one way only: Presentation → Domain → Data.

| Folder | Layer | Holds |
|---|---|---|
| `lib/network/` | Data | API client. HTTP only |
| `hooks/queries/` | Data → Domain | Query hooks that wrap the API client (caching, refetching, invalidation) |
| `hooks/domain/` | Domain | Hooks that apply business rules to query data |
| `types/` | Domain | Domain types |
| `lib/utils/` | Domain | Pure functions and pure reducers |
| `components/` | Presentation | Reusable UI that renders from props only |
| `pages/` | Presentation | Composition: take data from hooks, pass props to components |

### Rules

- Components never call the API client. Data comes through query hooks only.
- Pages compose. They get data and logic from hooks and pass props to components.
- Business logic (filtering, validation, formatting) lives in domain hooks or pure functions, never in components or pages.
- No reverse dependencies: Data never imports Domain or Presentation; Domain never imports Presentation.
- Shared components hold no page-specific state and make no network calls.
- When state transitions are complex and have clear inputs and outputs, put a pure reducer in `lib/utils/` and test it without a DOM. The hook's effects do outside work (DOM measurement, timers, subscriptions) and only dispatch events. When an event leaves the state unchanged, return the same object so nothing re-renders. Keep one- or two-value state in `useState`.
- No hard-coded colors, spacing, or font sizes in components. Use design tokens; add a missing token to the token source first.
- When editing existing code in an area that does not follow these layers yet, separate that area in the same change, without touching unrelated areas.

### Tests

- Pure functions and reducers: unit tests, no DOM.
- Components: render with props; no network.
- User flows across pages: end-to-end tests against a test backend.
````

## Review checklist

- No API client import in `components/` or `pages/`.
- Pages contain no filtering, validation, or formatting logic beyond wiring.
- Shared components take props only; no new network call or page-specific state.
- Imports respect Presentation → Domain → Data; nothing in Data imports upward.
- New business rules are pure functions or domain hooks, with unit tests.
- Reducers are used only where transitions are complex; effects dispatch events and do not compute next state.
- No hard-coded design values; new values become tokens.
- Query keys for new data are consistent with existing invalidation.
- Structural changes are reflected in this document.
