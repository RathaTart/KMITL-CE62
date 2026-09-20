// 66011464 ราธา โรจน์รุจิพงศ์
// web worker js part

const bgColors = ['red', 'green', 'blue', 'yellow', 'black', 'grey'];
const txtColors = ['grey', 'black', 'yellow', 'blue', 'green', 'red'];
let colorIndex = 0; 
let timerID;


function getNextColors() {
    const selectedBgColor = bgColors[colorIndex];
    const selectedTxtColor = txtColors[colorIndex];
    colorIndex = (colorIndex + 1) % bgColors.length;
    return { bgColor: selectedBgColor, txtColor: selectedTxtColor };
}

function beginTimeUpdates() {
    timerID = setInterval(() => {
        const currentTimestamp = new Date(); 
        const colors = getNextColors();
        postMessage({
            date: currentTimestamp,
            backgroundColor: colors.bgColor,
            textColor: colors.txtColor,
        });
    }, 1000); //1 second
}


function stopTimeUpdates() {
    clearInterval(timerID);
}

onmessage = function (event) {
    if (event.data === 'start') {
        beginTimeUpdates();
    } else if (event.data === 'stop') {
        stopTimeUpdates();
    }
};
