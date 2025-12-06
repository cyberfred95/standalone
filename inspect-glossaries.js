const fs = require('fs');
const path = require('path');
require('dotenv').config({ path: path.join(__dirname, 'glossaires', '.env') });
const { Translator, Credentials } = require('@translated/lara');

async function inspect() {
    const accessKeyId = process.env.LARA_ACCESS_KEY_ID;
    const accessKeySecret = process.env.LARA_ACCESS_KEY_SECRET;
    const credentials = new Credentials(accessKeyId, accessKeySecret);
    const lara = new Translator(credentials);

    console.log('Methods on lara.glossaries:');
    console.log(Object.getOwnPropertyNames(Object.getPrototypeOf(lara.glossaries)));

    // Try to list glossaries if a likely method exists
    try {
        if (lara.glossaries.list) {
            console.log('Calling list()...');
            const list = await lara.glossaries.list();
            console.log('List result:', JSON.stringify(list, null, 2));
        } else if (lara.glossaries.getAll) {
            console.log('Calling getAll()...');
            const list = await lara.glossaries.getAll();
            console.log('List result:', JSON.stringify(list, null, 2));
        } else {
            console.log('No obvious list method found.');
        }
    } catch (e) {
        console.error('Error calling list method:', e.message);
    }
}

inspect();
