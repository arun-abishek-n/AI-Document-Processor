const TECH_STACK = ["React", "TypeScript", "Vite", "Tailwind CSS", "FastAPI", "EasyOCR", "OpenCV", "PyMuPDF"];

export function Footer() {
  return (
    <footer className="mt-16 border-t border-slate-200 py-8 dark:border-slate-800">
      <div className="mx-auto flex max-w-6xl flex-col items-center gap-3 px-4 text-center sm:px-6">
        <div className="flex flex-wrap justify-center gap-x-4 gap-y-1">
          {TECH_STACK.map((tech) => (
            <span key={tech} className="text-xs font-medium text-slate-400 dark:text-slate-500">
              {tech}
            </span>
          ))}
        </div>
        <p className="text-xs text-slate-400 dark:text-slate-500">
          Built by{" "}
          <a
            href="https://github.com/arun-abishek-n"
            target="_blank"
            rel="noreferrer"
            className="font-medium text-slate-500 hover:text-indigo-600 dark:text-slate-400 dark:hover:text-indigo-400"
          >
            Arun Abishek
          </a>{" "}
          — portfolio project, no proprietary data or code.
        </p>
      </div>
    </footer>
  );
}
