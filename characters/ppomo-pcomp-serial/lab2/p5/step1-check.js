// variable to hold an instance of the p5.webserial library:
const serial = new p5.WebSerial();

function setup() {
  // check to see if serial is available:
  if (!navigator.serial) {
    alert("WebSerial is not supported in this browser. Try Chrome or MS Edge.");
  }
}
