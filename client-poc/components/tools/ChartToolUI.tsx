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
  YAxis,
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import React from "react";
import GitHubDataFlow from "../flow/GitHubDataFlow";

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
  sql: string;
  type: "area" | "bar" | "line";
  title: string;
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
      type="linear"
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
      type="linear"
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

const formatXAxis = (tick: string) => {
  const date = new Date(tick);
  if (date.toString() !== "Invalid Date") {
    return date.toISOString().split("T")[0]; // This will return YYYY-MM-DD
  }
  return tick;
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
          tickFormatter={(tick) => formatXAxis(tick)}
          tickMargin={10}
          tickLine={false}
          axisLine={false}
        />
        <YAxis tickMargin={10} tickLine={false} axisLine={false} />
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

function extractTableNameFromQuery(sql: string): string | null {
  // This regex looks for the word "FROM" (case-insensitive),
  // then captures one or more non-whitespace characters (the table name).
  // The 'i' flag makes it case-insensitive.
  const fromRegex = /\bfrom\s+([^\s]+)\b/i;

  const match = sql.match(fromRegex);
  return match ? match[1] : null;
}

export const ChartToolUI = makeAssistantToolUI<
  Record<string, never>,
  ChartConfig
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

    if (!result.rows.length)
      return (
        <div className="flex items-center gap-1">
          <MousePointerClickIcon className="size-4" />
          <span>Queried Relta</span>
        </div>
      );

    return (
      <Tabs defaultValue="account" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="chart">Chart</TabsTrigger>
          <TabsTrigger value="sql">Generated SQL</TabsTrigger>
          <TabsTrigger value="semantic-layer">Data Flow</TabsTrigger>
        </TabsList>
        <TabsContent value="chart">
          <Card>
            <CardHeader className="py-4 text-center">{result.title}</CardHeader>
            <CardContent className="pb-4">
              <MyChart config={result} />
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="sql">
          <pre className="whitespace-pre-wrap border rounded-lg p-4 bg-muted/50">
            <code>{result.sql}</code>
          </pre>
        </TabsContent>
        <TabsContent value="semantic-layer">
          <GitHubDataFlow
            table={extractTableNameFromQuery(result.sql) ?? "Relta"}
          />
        </TabsContent>
      </Tabs>
    );
  },
});
