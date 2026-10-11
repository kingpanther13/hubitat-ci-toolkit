// Adapted from hubitat-local-mcp-server at 0e6094bf (MIT); see reference/provenance.json.
package support

/** Records three-argument device subscriptions and dispatches synthetic events by source identity. */
class SubscriptionRecorder {
    static class Subscription {
        Object source
        String attribute
        String handler
    }

    final List<Subscription> subscriptions = []

    /** The sample app uses subscribe(source, attribute, handler); extend for other overloads. */
    void record(Object source, String attribute, String handler) {
        subscriptions << new Subscription(
            source: source, attribute: attribute, handler: handler)
    }

    /**
     * Locate subscriptions matching the given source + attribute and
     * invoke each recorded handler on the loaded script with a synthetic
     * event. The event Map mirrors the shape the hub dispatches at
     * runtime: {@code device}, {@code name}, {@code value}. Overrides
     * merge into the event Map after the defaults so a spec can add
     * {@code isStateChange}, {@code source}, etc.
     *
     * For location-attribute subscriptions (mode, hsmStatus) the source
     * is the location-like instance — pass the same instance here
     * and the match fires. A plain-value source would fail identity
     * comparison, which is the behavior we want: callers should use the
     * exact object they passed into subscribe.
     *
     * Each handler is dispatched with its own shallow copy of the event
     * map. Production handlers don't mutate their event argument today,
     * but the defensive copy pre-empts cross-handler side effects if that
     * changes — without paying the cost of cloning per-key values (the
     * {@code device} reference etc. are still shared across copies).
     *
     * Throws {@link IllegalStateException} if no matching subscription
     * is found — silent no-op would be a test-authoring footgun.
     */
    List<Object> fireEvent(Object script, Object source, String attribute, Object value, Map overrides = [:]) {
        def matches = subscriptions.findAll {
            it.source.is(source) && it.attribute == attribute
        }
        if (matches.isEmpty()) {
            throw new IllegalStateException(
                "fireEvent(source=${source}, attribute=${attribute}) found no " +
                "matching subscription. Check that initialize() ran and " +
                "that the source instance matches (identity compare, not equality).")
        }
        Map event = [
            device: source,
            name: attribute,
            value: value
        ]
        event.putAll(overrides)
        matches.collect { Subscription sub -> script."${sub.handler}"(new LinkedHashMap(event)) }
    }

    /** Clear captured subscriptions when an app calls unsubscribe(). */
    void reset() {
        subscriptions.clear()
    }
}
