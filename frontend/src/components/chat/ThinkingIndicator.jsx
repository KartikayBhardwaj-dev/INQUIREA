"use client";

import { motion } from "framer-motion";

export default function ThinkingIndicator() {
  return (
    <div className="flex items-start gap-3 px-4 py-4 sm:px-8">
      {/* AI Icon */}
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-white text-sm font-semibold text-black">
        AI
      </div>

      {/* Thinking Bubble */}
      <div className="rounded-2xl rounded-tl-md border border-white/10 bg-white/[0.06] px-4 py-3">
        <div className="flex items-center gap-3">
          <motion.div
            animate={{
              opacity: [0.4, 1, 0.4],
            }}
            transition={{
              duration: 1.2,
              repeat: Infinity,
            }}
            className="text-sm text-white/70"
          >
            Searching your emails...
          </motion.div>

          <div className="flex gap-1">
            {[0, 1, 2].map((item) => (
              <motion.span
                key={item}
                animate={{
                  y: [0, -3, 0],
                }}
                transition={{
                  duration: 0.7,
                  repeat: Infinity,
                  delay: item * 0.12,
                }}
                className="h-1.5 w-1.5 rounded-full bg-white/60"
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}