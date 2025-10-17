import React from "react";

type Evidence = {
  type: string;
  detail: string;
  span?: string;
};

type Props = {
  ev: Evidence[];
};

export default function EvidenceChips({ ev }: Props) {
  if (!ev?.length) return null;
  return (
    <div>
      {ev.map((item, idx) => (
        <span key={idx} className="chip">
          <strong style={{ marginRight: 4 }}>{item.type}</strong>
          {item.detail}
        </span>
      ))}
    </div>
  );
}
