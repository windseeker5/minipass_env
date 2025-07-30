document.addEventListener("DOMContentLoaded", function () {
    const video = document.createElement("video");
    const canvasElement = document.getElementById("qr-canvas");
    const canvas = canvasElement.getContext("2d");

    function startQRScanner() {
        navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } })
            .then(function (stream) {
                video.srcObject = stream;
                video.setAttribute("playsinline", true);
                video.play();
                requestAnimationFrame(scanQRCode);
            });
    }

    function scanQRCode() {
        if (video.readyState === video.HAVE_ENOUGH_DATA) {
            canvasElement.width = video.videoWidth;
            canvasElement.height = video.videoHeight;
            canvas.drawImage(video, 0, 0, canvasElement.width, canvasElement.height);
        }
        requestAnimationFrame(scanQRCode);
    }

    document.getElementById("start-scan").addEventListener("click", startQRScanner);
});
