if (
  "serviceWorker" in navigator &&
  (location.protocol === "https:" || location.hostname === "localhost")
) {
  window.addEventListener("load", () => {
    navigator.serviceWorker
      .register("./sw.js?v=72", { updateViaCache: "none" })
      .then((registration) => registration.update())
      .catch(() => {});
  });
}
