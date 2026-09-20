const backgrondcolor = ['red', 'green', 'blue', 'plum', 'lime', 'cyan'];
const textcolor = ['black', 'white', 'yellow', 'purple', 'red', 'brown'];
var i = 0;

function changeColors() {
    const currentBg = backgrondcolor[i];
    const currentTxt = textcolor[i];
    i = (i + 1) % backgrondcolor.length;
    return { bg: currentBg, txt: currentTxt };
}

var intervalID;

function startTime() {
    intervalID = setInterval(() => {
        const currentTime = new Date();
        const colors = changeColors();
        postMessage({ date: currentTime, backgroundColor: colors.bg, textColor: colors.txt });
    }, 1000);
}

function stopTime() {
    clearInterval(intervalID);
}

onmessage = function (e) {
    if (e.data === 'start') {
        startTime();
    } else if (e.data === 'stop') {
        stopTime();
    }
};