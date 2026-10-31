import type { Metadata } from "next";
import { NarsMatcherDemo } from "@/components/match/NarsMatcherDemo";

export const metadata: Metadata = {
  title: "NARS Matcher Demo — ShadeWise",
  description:
    "Try deterministic foundation shade matching on source-checked NARS shades — no OpenAI key required.",
};

export default function MatchPage() {
  return <NarsMatcherDemo />;
}
