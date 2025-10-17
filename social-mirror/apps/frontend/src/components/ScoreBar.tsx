import React from "react";

type Props = {
  score: number;
};

export default function ScoreBar({ score }: Props) {
  const pct = Math.min(1, Math.max(0, score));
  return (
    <div
      style={{
        flex: 1,
        height: 12,
        background: "#e5e7eb",
        borderRadius: 999,
        overflow: "hidden"
      }}
    >
      <div
        style={{
          width: `${Math.round(pct * 100)}%`,
          height: "100%",
          background: pct > 0.6 ? "#16a34a" : "#fbbf24"
        }}
      />
    </div>
  );
}
