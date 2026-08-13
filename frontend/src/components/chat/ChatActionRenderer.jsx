"use client";

import DraftCard from "./DraftCard";


export default function ChatActionRenderer({
  action,
}) {
  if (!action) {
    return null;
  }


  // -----------------------------------------------
  // Draft actions
  // -----------------------------------------------

  if (
    action.type === "draft"
  ) {
    return (
      <DraftCard
        draft={action.draft}
        action={action.action}
      />
    );
  }


  // -----------------------------------------------
  // Unknown tool
  // -----------------------------------------------

  return null;
}