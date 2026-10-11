library(
    name: 'Levels', namespace: 'toolkit', author: 'Hubitat CI Toolkit',
    description: 'Small shared helper used by the sample virtual dimmer.'
)

Integer boundedLevel(value) {
    return Math.max(0, Math.min(100, value as Integer))
}
