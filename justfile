run:
    py -m travelbrag

# Deploy to production
publish:
    npx netlify-cli -- deploy --prod --dir=site
