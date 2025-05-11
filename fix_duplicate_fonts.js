const fs = require('fs');

const filePath = 'c:/Users/rahul/OneDrive/Desktop/SLIDE.AI/webapp-frontend/src/components/KonvaTextToolbar.jsx';

// Read the file
let content = fs.readFileSync(filePath, 'utf8');

// Split the content into lines
const lines = content.split('\n');

// Find the line numbers of the fonts declarations
const fontsDeclarationLines = [];
lines.forEach((line, index) => {
  if (line.trim().startsWith('const fonts =')) {
    fontsDeclarationLines.push(index);
  }
});

console.log('Found fonts declarations at lines:', fontsDeclarationLines);

// If we found more than one declaration, comment out the second one
if (fontsDeclarationLines.length > 1) {
  const secondDeclarationLine = fontsDeclarationLines[1];
  
  // Comment out the second declaration and the entire array
  lines[secondDeclarationLine - 1] = '  // Google Fonts list (already defined above)';
  lines[secondDeclarationLine] = '  // const fonts = [';
  
  // Find the end of the array (the closing bracket and semicolon)
  let endLine = secondDeclarationLine + 1;
  while (endLine < lines.length && !lines[endLine].includes('];')) {
    lines[endLine] = '  // ' + lines[endLine];
    endLine++;
  }
  
  if (endLine < lines.length) {
    lines[endLine] = '  // ' + lines[endLine];
  }
  
  // Write the modified content back to the file
  fs.writeFileSync(filePath, lines.join('\n'));
  
  console.log('Successfully commented out the duplicate fonts declaration');
} else {
  console.log('No duplicate fonts declaration found');
}
