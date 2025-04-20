import { useEffect, useRef } from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ChartOptions,
  ChartData
} from "chart.js";
import { Line } from "react-chartjs-2";
import { ChartPoint } from "@/lib/types";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

interface ChartComponentProps {
  ticker: string;
  data: ChartPoint[];
  entryPrice?: number;
  targetPrice?: number;
  stopLossPrice?: number;
  isLong?: boolean;
}

export default function ChartComponent({
  ticker,
  data,
  entryPrice,
  targetPrice,
  stopLossPrice,
  isLong = true
}: ChartComponentProps) {
  const chartRef = useRef<ChartJS>(null);

  // Calculate y-axis padding based on the price extremes
  const getYAxisBounds = () => {
    if (!data || data.length === 0) return { min: 0, max: 100 };

    const prices = data.map(point => point.price);
    const minPrice = Math.min(...prices);
    const maxPrice = Math.max(...prices);
    
    // Add lines for entry, target, and stop loss prices if provided
    const pricesToConsider = [minPrice, maxPrice];
    if (entryPrice) pricesToConsider.push(entryPrice);
    if (targetPrice) pricesToConsider.push(targetPrice);
    if (stopLossPrice) pricesToConsider.push(stopLossPrice);
    
    const absoluteMin = Math.min(...pricesToConsider);
    const absoluteMax = Math.max(...pricesToConsider);
    
    // Add padding
    const range = absoluteMax - absoluteMin;
    const padding = range * 0.1; // 10% padding
    
    return {
      min: absoluteMin - padding,
      max: absoluteMax + padding
    };
  };

  const chartData: ChartData<"line"> = {
    labels: data.map(point => point.time),
    datasets: [
      {
        label: ticker,
        data: data.map(point => point.price),
        borderColor: "rgba(99, 102, 241, 1)",
        backgroundColor: "rgba(99, 102, 241, 0.1)",
        borderWidth: 2,
        pointRadius: 0,
        pointHoverRadius: 4,
        tension: 0.1,
        fill: true
      }
    ]
  };

  const { min: yMin, max: yMax } = getYAxisBounds();

  const chartOptions: ChartOptions<"line"> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false
      },
      tooltip: {
        mode: "index",
        intersect: false,
        backgroundColor: "#1e1e1e",
        titleColor: "#f3f4f6",
        bodyColor: "#f3f4f6",
        borderColor: "#4b5563",
        borderWidth: 1,
        padding: 10,
        displayColors: false,
        callbacks: {
          label: function(context) {
            return `Price: ${context.parsed.y.toFixed(6)}`;
          }
        }
      }
    },
    scales: {
      x: {
        display: true,
        grid: {
          display: false,
          color: "rgba(75, 85, 99, 0.2)"
        },
        ticks: {
          color: "#9ca3af",
          maxTicksLimit: 6,
          font: {
            size: 10
          }
        }
      },
      y: {
        display: true,
        min: yMin,
        max: yMax,
        grid: {
          color: "rgba(75, 85, 99, 0.2)"
        },
        ticks: {
          color: "#9ca3af",
          font: {
            size: 10
          }
        }
      }
    },
    interaction: {
      mode: "nearest",
      intersect: false
    },
    animation: false
  };

  useEffect(() => {
    const chart = chartRef.current;
    if (!chart) return;

    // Add horizontal lines for entry, target, and stop loss
    chart.options.plugins.annotation = {
      annotations: {}
    };

    if (entryPrice) {
      chart.options.plugins.annotation.annotations.entry = {
        type: 'line',
        yMin: entryPrice,
        yMax: entryPrice,
        borderColor: 'rgba(255, 255, 255, 0.7)',
        borderWidth: 1,
        borderDash: [5, 5],
        label: {
          content: 'Entry',
          display: true,
          position: 'right',
          backgroundColor: 'rgba(30, 30, 30, 0.8)',
          font: {
            size: 10
          }
        }
      };
    }

    if (targetPrice) {
      chart.options.plugins.annotation.annotations.target = {
        type: 'line',
        yMin: targetPrice,
        yMax: targetPrice,
        borderColor: isLong ? 'rgba(34, 197, 94, 0.7)' : 'rgba(239, 68, 68, 0.7)',
        borderWidth: 1,
        borderDash: [2, 2],
        label: {
          content: 'Target',
          display: true,
          position: 'right',
          backgroundColor: 'rgba(30, 30, 30, 0.8)',
          font: {
            size: 10
          }
        }
      };
    }

    if (stopLossPrice) {
      chart.options.plugins.annotation.annotations.stopLoss = {
        type: 'line',
        yMin: stopLossPrice,
        yMax: stopLossPrice,
        borderColor: isLong ? 'rgba(239, 68, 68, 0.7)' : 'rgba(34, 197, 94, 0.7)',
        borderWidth: 1,
        borderDash: [2, 2],
        label: {
          content: 'SL',
          display: true,
          position: 'right',
          backgroundColor: 'rgba(30, 30, 30, 0.8)',
          font: {
            size: 10
          }
        }
      };
    }

    chart.update();
  }, [chartRef, data, entryPrice, targetPrice, stopLossPrice, isLong]);

  return (
    <div className="chart-container rounded-lg overflow-hidden h-full">
      <Line ref={chartRef} data={chartData} options={chartOptions} />
    </div>
  );
}
