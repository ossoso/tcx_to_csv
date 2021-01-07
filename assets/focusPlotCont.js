window.dash_clientside = Object.assign({}, window.dash_clientside, {
  clientside: {
    focusPlots: function () {
      document
        .getElementById("graphing-container")
        .scrollIntoView({ behavior: "smooth" });
      return;
    },
  },
});
