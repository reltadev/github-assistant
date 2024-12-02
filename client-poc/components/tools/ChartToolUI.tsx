"use client";

import { FC } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  XAxis,
} from "recharts";
import { makeAssistantToolUI } from "@assistant-ui/react";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  ChartLegend,
  ChartLegendContent,
} from "@/components/ui/chart";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { MousePointerClickIcon } from "lucide-react";

const getColumns = (data: object[]) => {
  const [xAxis, ...yAxis] = data.reduce<string[]>((acc, row) => {
    Object.keys(row).forEach((key) => {
      if (!acc.includes(key)) {
        acc.push(key);
      }
    });
    return acc;
  }, []);

  if (!xAxis || !yAxis.length) {
    return null;
  }
  return {
    xAxis,
    yAxis,
  };
};

type ChartConfig = {
  rows: object[];
  type: "area" | "bar" | "line";
};

const toFirstLetterUpperCase = (str: string) => {
  return str.charAt(0).toUpperCase() + str.slice(1);
};

const getChart = (type: "area" | "bar" | "line") => {
  switch (type) {
    case "area":
      return AreaChart;
    case "bar":
      return BarChart;
    case "line":
      return LineChart;
    default:
      const _exhaustiveCheck: never = type;
      throw new Error("Invalid chart type " + _exhaustiveCheck);
  }
};

type SeriesProps = {
  dataKey: string;
  fill: string;
};

const BarSeries: FC<SeriesProps> = ({ dataKey, fill }) => {
  return <Bar key={dataKey} dataKey={dataKey} fill={fill} radius={4} />;
};

const AreaSeries: FC<SeriesProps> = ({ dataKey, fill }) => {
  return (
    <Area
      key={dataKey}
      dataKey={dataKey}
      type="natural"
      fill={fill}
      fillOpacity={0.4}
      stroke={fill}
    />
  );
};

const LineSeries: FC<SeriesProps> = ({ dataKey, fill }) => {
  return (
    <Line
      key={dataKey}
      dataKey={dataKey}
      type="natural"
      stroke={fill}
      strokeWidth={2}
      dot={false}
    />
  );
};

const getChartSeries = (type: "area" | "bar" | "line") => {
  switch (type) {
    case "area":
      return AreaSeries;
    case "bar":
      return BarSeries;
    case "line":
      return LineSeries;
    default:
      const _exhaustiveCheck: never = type;
      throw new Error("Invalid chart type " + _exhaustiveCheck);
  }
};

const MyChart: FC<{ config: ChartConfig }> = ({ config }) => {
  const columns = getColumns(config.rows);
  if (!columns) return null;
  const { xAxis, yAxis } = columns;

  const chartConfig = Object.fromEntries(
    yAxis.map((axis) => [axis, { label: toFirstLetterUpperCase(axis) }])
  );

  const Chart = getChart(config.type);
  const getSeries = getChartSeries(config.type);

  return (
    <ChartContainer config={chartConfig} className="min-h-[200px] w-full">
      <Chart accessibilityLayer data={config.rows}>
        <CartesianGrid vertical={false} />
        <XAxis
          dataKey={xAxis}
          tickLine={false}
          tickMargin={10}
          axisLine={false}
          tickFormatter={(value) => value.slice(0, 3)}
        />
        <ChartTooltip content={<ChartTooltipContent />} />
        <ChartLegend content={<ChartLegendContent />} />
        {yAxis.map((axis, idx) =>
          getSeries({
            dataKey: axis,
            fill: `hsl(var(--chart-${idx + 1}))`,
          })
        )}
      </Chart>
    </ChartContainer>
  );
};

export const ChartToolUI = makeAssistantToolUI<
  Record<string, never>,
  {
    type: "area" | "bar" | "line";
    rows: object[];
  }
>({
  toolName: "chart",
  render: ({ result }) => {
    if (!result || typeof result !== "object")
      return (
        <div className="flex items-center gap-1 animate-pulse">
          <MousePointerClickIcon className="size-4" />
          <span>Querying Relta...</span>
        </div>
      );

    return (
      <Card>
        <CardHeader className="py-4 text-center">Chart</CardHeader>
        <CardContent className="pb-4">
          <MyChart config={result} />
        </CardContent>
      </Card>
    );
  },
});
