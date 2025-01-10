import { useState } from "react";
import "./App.css";
import { UploadButton } from "./components/upload-button";
import type { Analytics } from "./types/analytics";
import { AnalyticsCharts } from "./components/analytics-charts";
import ClusterVisualisation from "./components/cluster";

function App() {
  const [data, setData] = useState<Analytics | null>(null);

  const handleUploadSuccess = (analyticsData: Analytics) => {
    setData(analyticsData);
  };

  return (
    <>
      <div className="mx-auto max-w-7xl space-y-8 p-8">
        <div className="space-y-2">
          <h1 className="text-2xl font-semibold">Chat Analysis</h1>
          <p className="text-sm text-muted-foreground">
            Detailed metrics and insights about chat activity
          </p>
        </div>
        <UploadButton onSuccess={handleUploadSuccess} />
        {data && <AnalyticsCharts data={data} />}
      </div>
      {data && <ClusterVisualisation clusters={data.clusters} />}
    </>
  );
}

export default App;
