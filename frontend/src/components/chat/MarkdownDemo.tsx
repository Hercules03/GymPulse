
import ReactMarkdown from 'react-markdown';

// Demo component to showcase markdown rendering
const MarkdownDemo = () => {
  const sampleMarkdownText = `Here's what's available at **Hk Central Caine Branch**:

✅ **Cardio**: 17/24 available
✅ **Legs**: 9/14 available
✅ **Arms**: 10/10 available
✅ **Back**: 10/10 available
✅ **Other**: 7/8 available
✅ **Chest**: 10/14 available

Which type of workout are you interested in? 🏋️‍♂️`;

  return (
    <div className="max-w-md mx-auto p-6 bg-white rounded-2xl shadow-lg">
      <h2 className="text-lg font-bold mb-4">Before vs After Markdown Rendering</h2>

      <div className="space-y-6">
        {/* Before: Plain Text */}
        <div>
          <h3 className="text-sm font-semibold text-gray-600 mb-2">❌ Before (Plain Text)</h3>
          <div className="bg-gray-100 p-4 rounded-lg">
            <p className="text-sm text-gray-800 whitespace-pre-wrap">{sampleMarkdownText}</p>
          </div>
        </div>

        {/* After: Rendered Markdown */}
        <div>
          <h3 className="text-sm font-semibold text-green-600 mb-2">✅ After (Rendered Markdown)</h3>
          <div className="bg-gray-100 p-4 rounded-lg">
            <ReactMarkdown
              components={{
                p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
                em: ({ children }) => <em className="italic">{children}</em>,
                ul: ({ children }) => <ul className="list-disc list-inside space-y-1 mb-2">{children}</ul>,
                ol: ({ children }) => <ol className="list-decimal list-inside space-y-1 mb-2">{children}</ol>,
                li: ({ children }) => <li className="ml-2">{children}</li>,
              }}
            >
              {sampleMarkdownText}
            </ReactMarkdown>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MarkdownDemo;