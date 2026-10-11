/** Sample driver: a virtual switch with a bounded level. */
metadata {
    definition(name: 'CI Toolkit Virtual Dimmer', namespace: 'toolkit', author: 'Hubitat CI Toolkit') {
        capability 'Switch'
        capability 'SwitchLevel'
        capability 'Actuator'
    }
}

#include toolkit.Levels

def installed() {
    off()
    sendEvent(name: 'level', value: 0, unit: '%')
}
def updated() {}
def on() { sendEvent(name: 'switch', value: 'on') }
def off() { sendEvent(name: 'switch', value: 'off') }
def setLevel(value, duration = null) {
    Integer level = boundedLevel(value)
    sendEvent(name: 'level', value: level, unit: '%')
    sendEvent(name: 'switch', value: level > 0 ? 'on' : 'off')
}
