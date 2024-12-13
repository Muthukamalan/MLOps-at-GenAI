"use client";

import { Card, CardHeader, CardFooter } from "@nextui-org/card";
import { Image } from "@nextui-org/image";
import { ArrowDownToLine, Trash } from "lucide-react";
import { Button } from "@nextui-org/button";
import { JobType, jobsAtom } from "@/lib/atoms";
import { useAtom } from "jotai";
import { useEffect } from "react";
import clsx from "clsx";
import { CircularProgress } from "@nextui-org/progress";
import { Link } from "@nextui-org/link";

const RESULT_FETCH_INTERVAL = 5 * 1000;

const ImageJob = ({ job }: { job: JobType }) => {
  const [jobs, setJobs] = useAtom(jobsAtom);

  useEffect(() => {
    if (job.status === "PENDING") {
      const retry = setInterval(async () => {
        // console.log(job);

        try {
          const response = await fetch(
            `${process.env.NEXT_PUBLIC_BACKEND_URL}/results/${job.jobId}`,
            {
              method: "GET",
            }
          );

          const resJson = await response.json();

          if (resJson["status"] === "ERROR") {
            setJobs([
              ...jobs.map((j) => {
                if (j.jobId === job.jobId) {
                  j.status = "ERROR";
                  return j;
                }

                return j;
              }),
            ]);

            clearInterval(retry);
          }

          if (resJson["status"] === "SUCCESS") {
            setJobs([
              ...jobs.map((j) => {
                if (j.jobId === job.jobId) {
                  j.url = resJson["url"];
                  j.status = "SUCCESS";
                  return j;
                }

                return j;
              }),
            ]);

            clearInterval(retry);
          }
        } catch (e) {}
      }, RESULT_FETCH_INTERVAL);

      return () => {
        clearInterval(retry);
      };
    }
  }, [job, jobs, setJobs]);

  return (
    <Card isFooterBlurred className="col-span-1 hover:scale-110 hover:z-20">
      <CardHeader className="absolute z-10 top-1 flex-row justify-end gap-2 w-full">
        <Button
          className="bg-opacity-80 p-2"
          isIconOnly
          radius="lg"
          size="sm"
          color="danger"
          aria-label="Remove Image"
          onClick={() => {
            setJobs(jobs.filter((j) => j !== job));
          }}
        >
          <Trash />
        </Button>
        <Link href={job.url} isDisabled={!job.url}>
          <Button
            className="bg-opacity-80 p-2"
            isIconOnly
            radius="lg"
            size="sm"
            color="primary"
            isDisabled={!job.url}
            aria-label="Download Image"
          >
            <ArrowDownToLine />
          </Button>
        </Link>
      </CardHeader>
      <div className="relative">
        <Image
          removeWrapper
          alt="Card background"
          className={clsx(
            "z-0 w-full h-full object-cover",
            !job.url && "aspect-square blur-md"
          )}
          // src="/images/result.jpeg"
          // fallbackSrc="https://via.placeholder.com/300x200"
          isLoading={!job.url}
          src={job.url}
        />
        {!job.url && (
          <CircularProgress
            aria-label="Loading..."
            className="absolute top-1/2 right-1/2 translate-x-1/2 -translate-y-[80%]"
          />
        )}
      </div>
      <CardFooter className="absolute bg-black/40 bottom-0 border-t-1 border-zinc-100/50 z-10 justify-between">
        <div className="flex flex-grow gap-2 items-center">
          <div className="flex flex-col">
            <p className="text-tiny text-white/60 font-bold">{job.prompt}</p>
          </div>
        </div>
      </CardFooter>
    </Card>
  );
};

export const ImagesGrid = () => {
  const [jobs, setJobs] = useAtom(jobsAtom);

  return (
    <div className="w-full gap-6 grid grid-cols-1 mt-12 md:grid-cols-2 lg:grid-cols-4">
      {jobs.map((job, i) => (
        <ImageJob job={job} key={i} />
      ))}
    </div>
  );
};
