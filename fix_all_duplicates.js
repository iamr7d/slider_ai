const fs = require('fs');

const filePath = 'c:/Users/rahul/OneDrive/Desktop/SLIDE.AI/webapp-frontend/src/components/KonvaTextToolbar.jsx';

// Read the file
let content = fs.readFileSync(filePath, 'utf8');

// Split the content into lines
const lines = content.split('\n');

// List of function/variable declarations to check for duplicates
const declarationsToCheck = [
  'handleFontFamilyChange',
  'filteredFonts',
  'startX',
  'startY',
  'handleBoldClick',
  'handleItalicClick',
  'handleAlignChange',
  'handleFontSizeChange',
  'handleColorChange',
  'handleColorButtonClick',
  'handleFontButtonClick',
  'isBold',
  'isItalic',
  'currentAlign'
];

// Find all declarations and their line numbers
const declarationLines = {};

declarationsToCheck.forEach(declaration => {
  declarationLines[declaration] = [];
});

// Find all declarations in the file
lines.forEach((line, index) => {
  declarationsToCheck.forEach(declaration => {
    if (line.trim().startsWith(`const ${declaration} =`) || 
        line.trim().startsWith(`const ${declaration} =`) || 
        line.trim() === `const ${declaration} = () => {`) {
      declarationLines[declaration].push(index);
    }
  });
});

// Log what we found
console.log('Found declarations:');
Object.keys(declarationLines).forEach(declaration => {
  if (declarationLines[declaration].length > 0) {
    console.log(`${declaration}: ${declarationLines[declaration].join(', ')}`);
  }
});

// Comment out duplicate declarations
let changesMade = false;

Object.keys(declarationLines).forEach(declaration => {
  const lines = declarationLines[declaration];
  
  if (lines.length > 1) {
    // We have duplicates - comment out all but the first one
    for (let i = 1; i < lines.length; i++) {
      const lineIndex = lines[i];
      
      // Comment out the declaration line
      content = content.replace(
        new RegExp(`(\\s*)const ${declaration} =`, 'g'),
        (match, whitespace, offset) => {
          // Only replace occurrences after the first one
          if (content.indexOf(`const ${declaration} =`) < offset) {
            return `${whitespace}// Using ${declaration} defined earlier in the component\n${whitespace}// const ${declaration} =`;
          }
          return match;
        }
      );
      
      changesMade = true;
    }
  }
});

if (changesMade) {
  // Write the modified content back to the file
  fs.writeFileSync(filePath, content);
  console.log('Successfully commented out duplicate declarations');
} else {
  console.log('No duplicate declarations found or changes needed');
}

// Now let's handle function bodies and object/array contents
// This is a more complex approach that would require parsing the code structure
// For simplicity, we'll manually comment out the known duplicates

// Check for handleFontFamilyChange duplicates
const handleFontFamilyChangePattern = /const handleFontFamilyChange = \(fontFamily\) => \{[\s\S]*?\};/g;
const matches = content.match(handleFontFamilyChangePattern);

if (matches && matches.length > 1) {
  // Keep the first occurrence, comment out the rest
  let firstOccurrence = true;
  content = content.replace(handleFontFamilyChangePattern, (match) => {
    if (firstOccurrence) {
      firstOccurrence = false;
      return match;
    } else {
      // Comment out each line of the function
      return '// ' + match.split('\n').join('\n// ');
    }
  });
  
  // Write the modified content back to the file
  fs.writeFileSync(filePath, content);
  console.log('Successfully commented out duplicate function bodies');
}
