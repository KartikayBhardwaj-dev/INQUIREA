"use client";

import ReactMarkdown from "react-markdown";

export default function MarkdownRenderer({ content }) {
  return (
    <div className="prose">
      <ReactMarkdown>{content}</ReactMarkdown>
    </div>
  );
}