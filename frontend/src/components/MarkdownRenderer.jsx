"use client";

import ReactMarkdown from "react-markdown";

export default function MarkdownRenderer({ content, children }) {
  // Support both `content` prop and children syntax
  const markdownContent = content ?? children;

  return (
    <div className="prose prose-invert max-w-none">
      <ReactMarkdown>{markdownContent}</ReactMarkdown>
    </div>
  );
}
