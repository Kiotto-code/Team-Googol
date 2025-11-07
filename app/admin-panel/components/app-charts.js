// import Chart from "chart.js/auto";
const Chart = window.Chart;

export function createPieChart({ labels, values }, options = {}) {
  const wrap = document.createElement("div");
  wrap.style.width = "100%";
  wrap.style.height = options.height || "250px";
  wrap.style.position = "relative";

  const canvas = document.createElement("canvas");
  wrap.appendChild(canvas);

  new Chart(canvas.getContext("2d"), {
    type: "pie",
    data: {
      labels,
      datasets: [
        {
          data: values,
        },
      ],
    },
    options: {
      responsive: true,
      plugins: {
        title: {
          display: !!options.title,
          text: options.title || "",
        },
        legend: {
          display: options.showLegend ?? true,
        },
      },
    },
  });

  return wrap;
}

export function createBarChart({ labels, values }, options = {}) {
  const wrap = document.createElement("div");
  wrap.style.width = "100%";
  wrap.style.height = options.height || "250px";
  wrap.style.position = "relative";

  const canvas = document.createElement("canvas");
  wrap.appendChild(canvas);

  new Chart(canvas.getContext("2d"), {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          label: options.label || "Value",
          data: values,
        },
      ],
    },
    options: {
      responsive: true,
      plugins: {
        title: {
          display: !!options.title,
          text: options.title || "",
        },
        legend: {
          display: options.showLegend ?? false,
        },
      },
    },
  });

  return wrap;
}
