import {
  ScatterChart,
  Scatter,
  ResponsiveContainer,
  XAxis,
  YAxis,
  Tooltip,
  ZAxis,
} from "recharts";
import { ConversationClustersList } from "@/types/kura";
import { useMemo } from "react";

type ClusterMapProps = {
  clusters: ConversationClustersList;
};

const ClusterMap = ({ clusters }: ClusterMapProps) => {
  const nodeCoordinates = clusters.map((cluster) => ({
    label: cluster.name,
    x: cluster.x_coord,
    y: cluster.y_coord,
    id: cluster.id,
  }));

  // Calculate bounds for scaling
  const { minX, maxX, minY, maxY, xRange, yRange } = useMemo(() => {
    const xValues = nodeCoordinates.map((node) => node.x);
    const yValues = nodeCoordinates.map((node) => node.y);

    const minX = Math.min(...xValues);
    const maxX = Math.max(...xValues);
    const minY = Math.min(...yValues);
    const maxY = Math.max(...yValues);

    return {
      minX,
      maxX,
      minY,
      maxY,
      xRange: maxX - minX,
      yRange: maxY - minY,
    };
  }, [nodeCoordinates]);

  return (
    <ResponsiveContainer>
      <ScatterChart
        margin={{
          top: 20,
          right: 20,
          bottom: 20,
          left: 20,
        }}
        width={1000}
        height={1000}
      >
        <Tooltip
          cursor={{ strokeDasharray: "3 3" }}
          content={({ payload }) => {
            if (payload && payload[0]) {
              return (
                <div className="bg-white p-2 border rounded shadow">
                  {payload[0].payload.label}
                </div>
              );
            }
            return null;
          }}
        />
        <XAxis
          type="number"
          dataKey="x"
          domain={[minX - xRange * 0.05, maxX + xRange * 0.05]}
          name="X"
          tickFormatter={(value) => value.toFixed(2)}
        />
        <YAxis
          type="number"
          dataKey="y"
          domain={[minY - yRange * 0.05, maxY + yRange * 0.05]}
          name="Y"
          tickFormatter={(value) => value.toFixed(2)}
        />
        <ZAxis range={[50, 200]} />
        <Scatter
          name="Clusters"
          data={nodeCoordinates}
          fill="#8884d8"
          cursor="pointer"
        />
      </ScatterChart>
    </ResponsiveContainer>
  );
};

export default ClusterMap;
