import SwiftUI
import WebKit

@main
struct AtlasApp: App {
    var body: some Scene {
        WindowGroup { AtlasView() }
    }
}

struct AtlasView: UIViewRepresentable {
    func makeUIView(context: Context) -> WKWebView {
        let view = WKWebView(frame: .zero)
        view.scrollView.bounces = false
        if let page = Bundle.main.url(forResource: "Atlas", withExtension: "html") {
            view.loadFileURL(page, allowingReadAccessTo: page.deletingLastPathComponent())
        }
        return view
    }

    func updateUIView(_ view: WKWebView, context: Context) {}
}
