import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Cluster } from '../lib/api';
import { ScatterChart, Scatter, XAxis, YAxis, ZAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

interface ClusterMapProps {
  clusters: Cluster[];
}

interface ChartData {
  x: number;
  y: number;
  z: number;
  id: string;
  name: string;
  description: string;
  frustration: number;
  conversationCount: number;
  level: number;
}

export default function ClusterMap({ clusters }: ClusterMapProps) {
  const navigate = useNavigate();
  const [hoveredCluster, setHoveredCluster] = useState<string | null>(null);

  // Prepare data for the scatter chart
  const data: ChartData[] = clusters.map(cluster => ({
    x: cluster.x_coord,
    y: cluster.y_coord,
    z: cluster.conversation_count || 10,
    id: cluster.id,
    name: cluster.name,
    description: cluster.description,
    frustration: cluster.avg_frustration || 0,
    conversationCount: cluster.conversation_count || 0,
    level: cluster.level,
  }));

  // Color scale based on frustration level
  const getColor = (frustration: number) => {
    if (frustration <= 2) return '#10b981'; // green
    if (frustration <= 3) return '#3b82f6'; // blue
    if (frustration <= 4) return '#f59e0b'; // orange
    return '#ef4444'; // red
  };

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-popover text-popover-foreground border rounded-lg shadow-lg p-3">
          <p className="font-semibold">{data.name}</p>
          <p className="text-sm text-muted-foreground mb-2">{data.description}</p>
          <div className="space-y-1 text-sm">
            <p>Conversations: <span className="font-medium">{data.conversationCount}</span></p>
            <p>Avg Frustration: <span className="font-medium">{data.frustration.toFixed(1)}/5</span></p>
            <p>Level: <span className="font-medium">{data.level}</span></p>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="space-y-4">
      {/* Legend */}
      <div className="flex items-center gap-4 text-sm">
        <span className="text-muted-foreground">Frustration Level:</span>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-green-500" />
          <span>Low (≤2)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-blue-500" />
          <span>Medium (2-3)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-orange-500" />
          <span>High (3-4)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-red-500" />
          <span>Very High (&gt;4)</span>
        </div>
      </div>

      {/* Chart */}
      <div className="h-[600px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart
            margin={{ top: 20, right: 20, bottom: 20, left: 20 }}
          >
            <XAxis 
              type="number" 
              dataKey="x" 
              name="X" 
              domain={['dataMin - 5', 'dataMax + 5']}
              tick={{ fontSize: 12 }}
            />
            <YAxis 
              type="number" 
              dataKey="y" 
              name="Y" 
              domain={['dataMin - 5', 'dataMax + 5']}
              tick={{ fontSize: 12 }}
            />
            <ZAxis 
              type="number" 
              dataKey="z" 
              range={[50, 400]} 
              name="Conversations"
            />
            <Tooltip 
              content={<CustomTooltip />}
              cursor={{ strokeDasharray: '3 3' }}
            />
            <Scatter
              data={data}
              className="cursor-pointer"
              onClick={(data: any) => navigate(`/clusters/${data.id}`)}
              onMouseEnter={(data: any) => setHoveredCluster(data.id)}
              onMouseLeave={() => setHoveredCluster(null)}
            >
              {data.map((entry, index) => (
                <Cell 
                  key={`cell-${index}`} 
                  fill={getColor(entry.frustration)}
                  stroke={hoveredCluster === entry.id ? '#000' : 'none'}
                  strokeWidth={hoveredCluster === entry.id ? 2 : 0}
                  fillOpacity={hoveredCluster && hoveredCluster !== entry.id ? 0.3 : 0.8}
                />
              ))}
            </Scatter>
          </ScatterChart>
        </ResponsiveContainer>
      </div>

      {/* Instructions */}
      <div className="text-sm text-muted-foreground text-center">
        Click on any cluster to view details. Bubble size represents the number of conversations.
      </div>
    </div>
  );
}