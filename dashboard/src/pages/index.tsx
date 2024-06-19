import Head from "next/head";
import Link from "next/link";

export default function Home() {
  return (
    <>
      <Head>
        <title>Lexy AI</title>
        <meta name="description" content="Lexy AI is a data platform for building AI powered applications" />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      <main className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-b from-[#2e026d] to-[#15162c]">
        <div className="container flex flex-col items-center justify-center gap-12 px-4 py-16 ">
          <h1 className="text-5xl font-extrabold tracking-tight text-white sm:text-[5rem] text-center">
            Data pipelines for <span className="text-[hsl(280,100%,70%)]">AI</span> applications
          </h1>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3 md:gap-8">
            <Link
              className="flex max-w-xs flex-col gap-4 rounded-xl bg-white/10 p-4 text-white hover:bg-white/20"
              href="https://getlexy.com"
              target="_blank"
            >
              <h3 className="text-2xl font-bold">📚 Documentation</h3>
              <div className="text-lg">
                Online documentation for Lexy AI, including a quickstart guide, tutorials, and SDK reference.
              </div>
            </Link>
            <Link
              className="flex max-w-xs flex-col gap-4 rounded-xl bg-white/10 p-4 text-white hover:bg-white/20"
              href="http://localhost:9900/docs"
              target="_blank"
            >
              <h3 className="text-2xl font-bold">🚀 REST API</h3>
              <div className="text-lg">
                Learn more about the Lexy API, and try out the various endpoints.
              </div>
            </Link>
            <Link
              className="flex max-w-xs flex-col gap-4 rounded-xl bg-white/10 p-4 text-white hover:bg-white/20"
              href="http://localhost:5556/tasks"
              target="_blank"
            >
              <h3 className="text-2xl font-bold">🛠 Task Monitor️</h3>
              <div className="text-lg">
                View recent tasks, including args, results, and tracebacks.
              </div>
            </Link>
          </div>
        </div>
      </main>
    </>
  );
}
