"use client";

import { jobsAtom } from "@/lib/atoms";
import { Button } from "@nextui-org/button";
import { Input } from "@nextui-org/input";
import { useAtom } from "jotai";
import { useState } from "react";

export const PromptInput = () => {
  const [jobs, setJobs] = useAtom(jobsAtom);
  const [textInput, setTextInput] = useState(
    "Line art for Casterly Rock castel with rivers in background"
  );
  const [submitting, setSubmitting] = useState(false);

  const onSubmit = async () => {
    setSubmitting(true);

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_BACKEND_URL}/text-to-image?text=${textInput}`,
        {
          method: "POST",
        }
      );

      const resJson = await response.json();
      //   console.log(results);

      setJobs([
        ...jobs,
        {
          jobId: resJson["job-id"],
          prompt: textInput,
          status: "PENDING",
          url: "",
        },
      ]);
    } catch (e) {
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="flex space-x-4 items-end w-full">
      <Input
        size="md"
        type="text"
        label="Prompt"
        value={textInput}
        labelPlacement="outside"
        onChange={(e) => {
          setTextInput(e.target.value ?? "");
        }}
      />
      <Button
        onClick={onSubmit}
        isDisabled={
          textInput.length < 10 ||
          jobs.filter((j) => j.status === "PENDING").length > 3
        }
        isLoading={submitting}
      >
        Submit
      </Button>
    </div>
  );
};
