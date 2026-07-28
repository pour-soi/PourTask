import QtQuick
import "../theme"

Item {
    id: icon
    property string name: ""
    property color iconColor: Theme.secondary
    implicitWidth: 18
    implicitHeight: 18

    Canvas {
        id: canvas
        anchors.fill: parent
        onPaint: {
            var c = getContext("2d")
            c.reset()
            c.strokeStyle = icon.iconColor
            c.fillStyle = icon.iconColor
            c.lineWidth = 1.6
            c.lineCap = "round"
            c.lineJoin = "round"
            var w = width, h = height
            if (icon.name === "inbox") {
                c.strokeRect(w * .18, h * .24, w * .64, h * .58)
                c.beginPath(); c.moveTo(w*.18,h*.58); c.lineTo(w*.38,h*.58); c.quadraticCurveTo(w*.5,h*.72,w*.62,h*.58); c.lineTo(w*.82,h*.58); c.stroke()
            } else if (icon.name === "today" || icon.name === "month") {
                c.strokeRect(w*.18,h*.22,w*.64,h*.62)
                c.beginPath(); c.moveTo(w*.18,h*.4); c.lineTo(w*.82,h*.4); c.moveTo(w*.34,h*.14); c.lineTo(w*.34,h*.3); c.moveTo(w*.66,h*.14); c.lineTo(w*.66,h*.3); c.stroke()
                if (icon.name === "today") { c.beginPath(); c.arc(w*.5,h*.62,w*.1,0,Math.PI*2); c.fill() }
            } else if (icon.name === "completed") {
                c.beginPath(); c.arc(w*.5,h*.5,w*.34,0,Math.PI*2); c.stroke(); c.beginPath(); c.moveTo(w*.32,h*.5); c.lineTo(w*.45,h*.64); c.lineTo(w*.7,h*.36); c.stroke()
            } else if (icon.name === "settings") {
                c.beginPath(); c.arc(w*.5,h*.5,w*.27,0,Math.PI*2); c.stroke(); c.beginPath(); c.arc(w*.5,h*.5,w*.08,0,Math.PI*2); c.stroke()
                for (var i=0;i<8;i++){ var a=i*Math.PI/4; c.beginPath(); c.moveTo(w*.5+Math.cos(a)*w*.29,h*.5+Math.sin(a)*h*.29); c.lineTo(w*.5+Math.cos(a)*w*.39,h*.5+Math.sin(a)*h*.39); c.stroke() }
            } else if (icon.name === "search") {
                c.beginPath(); c.arc(w*.43,h*.43,w*.25,0,Math.PI*2); c.stroke(); c.beginPath(); c.moveTo(w*.61,h*.61); c.lineTo(w*.82,h*.82); c.stroke()
            } else if (icon.name === "plus") {
                c.beginPath(); c.moveTo(w*.5,h*.22); c.lineTo(w*.5,h*.78); c.moveTo(w*.22,h*.5); c.lineTo(w*.78,h*.5); c.stroke()
            } else if (icon.name === "left" || icon.name === "right") {
                var direction = icon.name === "left" ? 1 : -1
                c.beginPath(); c.moveTo(w*(.5+.16*direction),h*.24); c.lineTo(w*(.5-.12*direction),h*.5); c.lineTo(w*(.5+.16*direction),h*.76); c.stroke()
            } else if (icon.name === "up" || icon.name === "down") {
                var vertical = icon.name === "up" ? 1 : -1
                c.beginPath(); c.moveTo(w*.24,h*(.5+.13*vertical)); c.lineTo(w*.5,h*(.5-.13*vertical)); c.lineTo(w*.76,h*(.5+.13*vertical)); c.stroke()
            } else if (icon.name === "open") {
                c.strokeRect(w*.18,h*.34,w*.48,h*.48)
                c.beginPath(); c.moveTo(w*.45,h*.18); c.lineTo(w*.82,h*.18); c.lineTo(w*.82,h*.55)
                c.moveTo(w*.82,h*.18); c.lineTo(w*.43,h*.57); c.stroke()
            }
        }
        Connections { target: icon; function onIconColorChanged() { canvas.requestPaint() } function onNameChanged() { canvas.requestPaint() } }
    }
}
