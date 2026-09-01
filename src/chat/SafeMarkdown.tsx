import ReactMarkdown from "react-markdown";
import { defaultUrlTransform } from "react-markdown";

const ALLOWED_ELEMENTS = ["p", "strong", "em", "ul", "ol", "li", "a", "br"];

function isSafeHref(href: string): boolean {
  const value = href.trim();
  const lower = value.toLowerCase();
  if (
    lower.startsWith("javascript:") ||
    lower.startsWith("data:") ||
    lower.startsWith("vbscript:") ||
    lower.startsWith("file:")
  ) {
    return false;
  }
  return /^(https?:\/\/|mailto:)/i.test(value);
}

function urlTransform(url: string): string {
  const transformed = defaultUrlTransform(url);
  return isSafeHref(transformed) ? transformed : "";
}

function prepareMarkdown(raw: string): string {
  return raw
    .replace(/\r\n/g, "\n")
    .replace(/\s+\*\s+(\*\*[^*]+\*\*)/g, "\n* $1")
    .replace(/\s+-\s+(\*\*[^*]+\*\*)/g, "\n- $1")
    .trim();
}

type SafeMarkdownProps = {
  text: string;
};

export function SafeMarkdown({ text }: SafeMarkdownProps) {
  return (
    <div className="chat-md text-sm leading-relaxed">
      <ReactMarkdown
        skipHtml
        unwrapDisallowed
        allowedElements={ALLOWED_ELEMENTS}
        urlTransform={urlTransform}
        components={{
          p: ({ children }) => <p className="mb-2 last:mb-0 whitespace-pre-wrap">{children}</p>,
          strong: ({ children }) => <strong className="font-semibold text-white">{children}</strong>,
          em: ({ children }) => <em className="italic">{children}</em>,
          ul: ({ children }) => <ul className="mb-2 list-disc space-y-1 pl-4 last:mb-0">{children}</ul>,
          ol: ({ children }) => <ol className="mb-2 list-decimal space-y-1 pl-4 last:mb-0">{children}</ol>,
          li: ({ children }) => <li className="pl-0.5">{children}</li>,
          a: ({ href, children }) =>
            href ? (
              <a
                href={href}
                target="_blank"
                rel="noopener noreferrer nofollow"
                className="underline decoration-cyan-400/70 underline-offset-2 hover:text-cyan-300"
              >
                {children}
              </a>
            ) : (
              <span>{children}</span>
            ),
        }}
      >
        {prepareMarkdown(text)}
      </ReactMarkdown>
    </div>
  );
}
