"use client";

import React, { useMemo } from "react";
import ReactFlow, { Node, Edge, Background, NodeTypes } from "reactflow";
import "reactflow/dist/style.css";
import { GitHubNode } from "./GitHubNode";
import { DatabaseNode } from "./DatabaseNode";
import { SemanticLayerNode } from "./SemanticLayerNode";
import { QueryNode } from "./QueryNode";
import { useParams } from "next/navigation";

const nodeTypes: NodeTypes = {
  github: GitHubNode,
  database: DatabaseNode,
  semanticLayer: SemanticLayerNode,
  query: QueryNode,
};

const initialNodes = (owner: string, repo: string, table: string): Node[] => [
  {
    id: "1",
    type: "github",
    position: { x: 250, y: 0 },
    data: { label: `${owner}/${repo}` },
  },
  {
    id: "2",
    type: "database",
    position: { x: 250, y: 150 },
    data: { label: "PostgreSQL" },
  },
  {
    id: "3",
    type: "semanticLayer",
    position: { x: 250, y: 300 },
    data: {
      label: (
        <>
          {table}
          <br />
          DuckDB Semantic Layer
        </>
      ),
    },
  },
  {
    id: "4",
    type: "query",
    position: { x: 250, y: 450 },
    data: { label: "SQL Query" },
  },
];

const initialEdges: Edge[] = [
  { id: "e1-2", source: "1", target: "2", animated: true },
  { id: "e2-3", source: "2", target: "3", animated: true },
  { id: "e3-4", source: "3", target: "4", animated: true },
];

export default function GitHubDataFlow({ table }: { table: string }) {
  const { owner, repo } = useParams() as { owner: string; repo: string };
  return (
    <div style={{ width: "100%", height: "600px" }}>
      <ReactFlow
        nodes={useMemo(
          () => initialNodes(owner, repo, table),
          [owner, repo, table]
        )}
        edges={initialEdges}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.2 }}
      >
        <Background />
      </ReactFlow>
    </div>
  );
}
