# Testing standards

Written fresh. Informed by the test-pyramid literature (Fowler — cited, not
copied) and Anthropic's guidance that agents need runnable checks
(https://code.claude.com/docs/en/best-practices).

## Rules

- **T-1 (MUST)** Every behavior change ships with at least one test that
  fails without the change. If you can't write that test, say so and why —
  that's a design smell, not a shortcut opportunity.
- **T-2 (MUST)** Test outcomes, not implementation: assert on returned
  values, persisted state, and emitted events — not on which private methods
  were called. Tests that break on refactors teach people to delete tests.
- **T-3 (MUST)** Cover the unhappy paths that production will hit: invalid
  input, absent records, permission denied, dependency timeout, duplicate
  submission. One happy-path test is a demo, not a test suite.
- **T-4 (MUST)** Tests are deterministic and independent: no wall-clock
  sleeps, no order dependence, no shared mutable fixtures, no real network.
  Flaky tests cost more than no tests — they train everyone to ignore red.
- **T-5 (SHOULD)** Shape follows the pyramid: many fast unit tests, some
  integration tests over real seams (DB, queue) with test instances, few
  end-to-end tests for the money paths (cf. Fowler, "The Practical Test
  Pyramid").
- **T-6 (SHOULD)** For pure logic with an invariant (round-trips, totals,
  ordering), add a property-based test (Hypothesis/fast-check) — it finds
  the edge cases nobody enumerates.
- **T-7 (SHOULD)** Prefer fakes/contract tests over deep mock choreography;
  a test with five mocks tests your mocks.

## Examples

Bad (violates T-2, T-3):

    def test_withdraw():
        svc.withdraw(acc, 50)
        assert repo.save.called          # implementation detail
                                          # ...and no test for overdraft at all

Good:

    def test_withdraw_reduces_balance():
        acc = make_account(balance=100)
        svc.withdraw(acc, 50)
        assert get_balance(acc.id) == 50

    def test_withdraw_over_balance_is_rejected_and_balance_unchanged():
        acc = make_account(balance=100)
        with pytest.raises(InsufficientFunds):
            svc.withdraw(acc, 150)
        assert get_balance(acc.id) == 100

Property test (T-6):

    @given(st.lists(st.integers()))
    def test_sort_is_idempotent(xs):
        assert sorted(sorted(xs)) == sorted(xs)

## For the Check phase

Each "Done means" line in the plan should name its check (a test, a command,
a threshold). A criterion nobody can run is an opinion.
