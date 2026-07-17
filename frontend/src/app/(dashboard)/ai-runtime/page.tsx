import React from "react";
import { RoadmapBanner } from "@/components/RoadmapBanner";

export default function AIRuntimeDashboard() {
  return (
    <div className="p-8">
      <RoadmapBanner reason="this entire page is a static mockup — no API calls are made yet" />
      <h1 className="text-2xl font-bold text-gray-900">Ollama Runtime & GPU Orchestrator</h1>
      <p className="text-gray-600 mt-2">Monitor local models, VRAM usage, and Tool Calling.</p>

      <div className="mt-8 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="rounded-xl border bg-white p-6 shadow-sm">
          <h3 className="text-lg font-medium text-gray-900">GPU VRAM (Simulated)</h3>
          <div className="mt-4">
            <div className="flex justify-between text-sm">
              <span>8.7 GB Used</span>
              <span>16.0 GB Total</span>
            </div>
            <div className="mt-2 w-full rounded-full bg-gray-200">
              <div className="h-2 rounded-full bg-blue-600" style={{ width: "54%" }}></div>
            </div>
          </div>
          <ul className="mt-4 space-y-2">
            <li className="flex justify-between text-sm border-b pb-2">
              <span>llama3.1:latest</span>
              <span className="text-gray-500">4.7 GB</span>
            </li>
            <li className="flex justify-between text-sm">
              <span>qwen2.5:latest</span>
              <span className="text-gray-500">4.0 GB</span>
            </li>
          </ul>
        </div>
        
        <div className="rounded-xl border bg-white p-6 shadow-sm">
          <h3 className="text-lg font-medium text-gray-900">Live Streaming Console</h3>
          <div className="mt-4 h-32 rounded bg-gray-900 p-4 text-sm text-green-400 font-mono overflow-y-auto">
            &gt; Receiving SSE stream...<br/>
            &gt; &lt;tool_call&gt; hybrid_rag(&quot;fraud&quot;) &lt;/tool_call&gt;<br/>
            &gt; Tool executed successfully.<br/>
          </div>
        </div>
      </div>
    </div>
  );
}
