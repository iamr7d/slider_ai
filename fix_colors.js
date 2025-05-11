const fs = require('fs');

const filePath = 'c:/Users/rahul/OneDrive/Desktop/SLIDE.AI/webapp-frontend/src/components/KonvaTextToolbar.jsx';

// Read the file
let content = fs.readFileSync(filePath, 'utf8');

// Replace the second declaration of colors with a comment
content = content.replace(
  /\/\/ Enhanced glassmorphic color palette with support for dark mode\s+const colors = isDarkMode \? \{/g, 
  (match, offset, string) => {
    // Only replace the second occurrence
    if (string.indexOf(match) < offset) {
      return "// Using the colors object defined earlier in the component";
    }
    return match;
  }
);

// Write the modified content back to the file
fs.writeFileSync(filePath, content);

console.log('File updated successfully!');
