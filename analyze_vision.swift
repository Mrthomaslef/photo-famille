import Foundation
import Vision
import AppKit

struct TagScore: Codable {
    let label: String
    let confidence: Float
}

struct ImageAnalysis: Codable {
    let filename: String
    let tags: [TagScore]
    let faceCount: Int
    let hasText: Bool
}

let fileManager = FileManager.default
let projectDir = URL(fileURLWithPath: "/Users/thomaslefevre/.t3/projects/photo-famille")
let photosDir = projectDir.appendingPathComponent("photos")
let outputURL = projectDir.appendingPathComponent("data/vision_analysis.json")

guard let files = try? fileManager.contentsOfDirectory(at: photosDir, includingPropertiesForKeys: nil) else {
    print("Cannot read photos dir")
    exit(1)
}

let jpgFiles = files.filter { $0.pathExtension.lowercased() == "jpg" }.sorted { $0.lastPathComponent < $1.lastPathComponent }
print("Analyzing \(jpgFiles.count) images with Apple Vision...")

var results: [String: ImageAnalysis] = [:]
let lock = NSLock()
let queue = OperationQueue()
queue.maxConcurrentOperationCount = 8

var processed = 0

for fileURL in jpgFiles {
    queue.addOperation {
        autoreleasepool {
            let filename = fileURL.lastPathComponent
            let classifyReq = VNClassifyImageRequest()
            let faceReq = VNDetectFaceRectanglesRequest()
            
            let handler = VNImageRequestHandler(url: fileURL, options: [:])
            do {
                try handler.perform([classifyReq, faceReq])
            } catch {
                // Ignore errors on tiny thumbs or corrupted files
            }
            
            var topTags: [TagScore] = []
            if let observations = classifyReq.results {
                for obs in observations where obs.confidence >= 0.15 {
                    topTags.append(TagScore(label: obs.identifier, confidence: obs.confidence))
                    if topTags.count >= 12 { break }
                }
            }
            
            let faces = faceReq.results?.count ?? 0
            let hasText = topTags.contains { $0.label.contains("document") || $0.label.contains("text") || $0.label.contains("screenshot") || $0.label.contains("diagram") }
            
            let analysis = ImageAnalysis(filename: filename, tags: topTags, faceCount: faces, hasText: hasText)
            
            lock.lock()
            results[filename] = analysis
            processed += 1
            if processed % 200 == 0 || processed == jpgFiles.count {
                print("  Processed \(processed)/\(jpgFiles.count)")
            }
            lock.unlock()
        }
    }
}

queue.waitUntilAllOperationsAreFinished()

let encoder = JSONEncoder()
if let data = try? encoder.encode(results) {
    try? data.write(to: outputURL)
    print("Saved Vision analysis to \(outputURL.path)")
}
