import { FindShadeIntro } from "@/components/FindShadeIntro";
import { FindShadeMoment } from "@/components/FindShadeMoment";
import { ShadeForm } from "@/components/ShadeForm";

export const metadata = {
  title: "Find Your Shade — ShadeWise",
  description:
    "Tell us about your foundation and get friendly guidance on what to try next.",
};

export default function FindYourShadePage() {
  return (
    <div>
      {/* Portrait lives here — with the headline */}
      <FindShadeIntro />

      {/* Form in the middle */}
      <div className="page-shell section-pad">
        <div className="mx-auto max-w-3xl">
          <ShadeForm />
        </div>
      </div>

      {/* Flatlay lives separately — after the form */}
      <FindShadeMoment />
    </div>
  );
}
