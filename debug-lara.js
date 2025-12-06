const fs = require('fs');
const path = require('path');
require('dotenv').config({ path: path.join(__dirname, 'glossaires', '.env') });
const { Translator, Credentials } = require('@translated/lara');

console.log('Starting debug script...');
console.log('LARA_ACCESS_KEY_ID:', process.env.LARA_ACCESS_KEY_ID ? 'Found' : 'Missing');
console.log('LARA_ACCESS_KEY_SECRET:', process.env.LARA_ACCESS_KEY_SECRET ? 'Found' : 'Missing');

try {
    const accessKeyId = process.env.LARA_ACCESS_KEY_ID;
    const accessKeySecret = process.env.LARA_ACCESS_KEY_SECRET;

    console.log('Creating Credentials...');
    const credentials = new Credentials(accessKeyId, accessKeySecret);

    console.log('Creating Translator...');
    const lara = new Translator(credentials);
    console.log('Translator created successfully.');

} catch (error) {
    console.error('CRASH:', error);
}
