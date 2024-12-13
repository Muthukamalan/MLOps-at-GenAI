import { ImagesGrid } from "@/components/images-grid";
import { PromptInput } from "@/components/prompt-input";

export default function Home() {
  return (
    <section className="max-w-[1280px]">
      <PromptInput />
      <ImagesGrid />
    </section>
  );
}
