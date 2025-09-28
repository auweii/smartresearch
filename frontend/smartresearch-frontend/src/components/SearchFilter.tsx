"use client";
import React from "react";
export default function SearchFilter({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  return (
    <div style={{ margin: "12px 0" }}>
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Search title / authors / topic…"
        style={{ width: "100%", padding: 10, borderRadius: 8, border: "1px solid #ddd" }}
      />
    </div>
  );
}
