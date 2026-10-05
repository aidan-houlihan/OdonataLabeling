# Odonata Label Studio

A static browser application for entering Darwin Core occurrence records and producing 5 x 3 inch preserved Odonata specimen labels. It can be hosted directly with GitHub Pages; no server or database is required.

## GitHub Pages
1. Create a GitHub repository.
2. Upload `index.html`, `style.css`, and `app.js` to the repository root.
3. Open **Settings -> Pages**.
4. Under **Build and deployment**, choose **Deploy from a branch**, then choose `main` and `/ (root)`.
5. Open the Pages URL GitHub provides.

The application stores data only in the browser while the page is open. Use **Export Records CSV** regularly to save entered occurrence data. Templates are downloaded as JSON files and can be loaded again later.

PDF creation uses jsPDF from jsDelivr, so the browser needs internet access when loading the page. The occurrence data itself is not uploaded to a server by this application.

## Features
- Darwin Core CSV import and CSV export.
- Symbiota-inspired occurrence editor grouped into Collector Info, Latest Identification, Locality, Misc, and Curation sections.
- Create, clone, navigate, edit, and delete many specimen records in one session.
- Label preview.
- Four 5 x 3 inch labels per US Letter sheet with shared internal edges to reduce cutting.
- Fixed identification block: scientificName, scientificNameAuthorship, identifiedBy, dateIdentified, followed by one blank line.
- Male/female symbol in upper-right from `sex`.
- Automatic USA when a recognized US state is present and country is blank.
- State and country bold on labels.
- Per-field include/exclude, order, prefix, suffix, separator, line break, blank lines, wrap width, font, font size, word spacing, and formatting.
- Save/load formatting templates.
