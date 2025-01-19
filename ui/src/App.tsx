import { useState } from "react";
import { UploadForm } from "./components/upload-form";
import type { Analytics } from "./types/analytics";
import { AnalyticsCharts } from "./components/analytics-charts";
import ClusterVisualisation from "./components/cluster";
import { Conversation } from "./types/conversation";

function App() {
  const [data, setData] = useState<Analytics | null>(null);
  const [allConversations, setAllConversations] = useState<Conversation[]>([]);

  const handleUploadSuccess = (analyticsData: Analytics) => {
    setData(analyticsData);
  };

  const resetData = () => {
    setData(null);
  };

  return (
    <>
      <div className="max-w-7xl mx-auto mb-10">
        <div className="space-y-8 p-8">
          <div className="space-y-2 text-center">
            <h1 className="text-2xl font-semibold">Chat Analysis</h1>
            <p className="text-sm text-muted-foreground">
              Detailed metrics and insights about chat activity
            </p>
          </div>
          <UploadForm
            onSuccess={handleUploadSuccess}
            resetData={resetData}
            setAllConversations={setAllConversations}
          />
          {data && <AnalyticsCharts data={data} />}
        </div>
      </div>

      {data && (
        <ClusterVisualisation
          conversations={allConversations}
          clusters={data.clusters}
        />
      )}
    </>
  );
}

export default App;
