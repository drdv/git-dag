document.addEventListener('DOMContentLoaded', function() {
    const svgObjects = document.querySelectorAll('object[type="image/svg+xml"]');

    svgObjects.forEach(function(svgObject) {
        svgObject.addEventListener('load', function() {
            const svgDoc = svgObject.contentDocument;
            const svgElement = svgDoc.querySelector('svg');

            // Initialize pan/zoom for each SVG element
            svgPanZoom(svgElement, {
                contain: false,
                fit: true,
                center: true,
                minZoom: 0.1,
                maxZoom: 30,
                zoomScaleSensitivity: 0.3,
                controlIconsEnabled: true,
		dblClickZoomEnabled: false
            });
        });
    });
});
