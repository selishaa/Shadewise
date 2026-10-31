import type { Metadata } from "next";
import { FoundationExplorer } from "@/components/explore/FoundationExplorer";

export const metadata: Metadata = {
  title: "Foundation Explorer — ShadeWise",
  description:
    "Search a historical archive of foundation shades across brands. Discovery only — not verified recommendations.",
};

export default function ExplorePage() {
  return <FoundationExplorer />;
}
