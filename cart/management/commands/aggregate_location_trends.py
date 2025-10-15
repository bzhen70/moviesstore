from django.core.management.base import BaseCommand
from datetime import date, timedelta
from cart.models import Order, Item, MovieLocationTrend
import json


class Command(BaseCommand):
    help = 'Aggregate order data by location to create movie location trends'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=30)
        parser.add_argument('--force', action='store_true')
        parser.add_argument('--export-json', action='store_true')
        parser.add_argument('--export-file', type=str, default='movie_trends.json')

    def handle(self, *args, **options):
        days_back = options['days']
        force_regenerate = options['force']
        export_json = options['export_json']
        export_file = options['export_file']
        
        end_date = date.today()
        start_date = end_date - timedelta(days=days_back)
        
        print(f'Aggregating orders from {start_date} to {end_date}')
        
        orders_with_location = Order.objects.filter(
            date__date__gte=start_date,
            date__date__lte=end_date,
            latitude__isnull=False,
            longitude__isnull=False
        )
        
        if not orders_with_location.exists():
            print('No orders with location data found')
            if export_json:
                self.export_for_google_maps(export_file)
            return
        
        print(f'Found {orders_with_location.count()} orders with location data')
        
        trends_created = 0
        trends_updated = 0
        
        for order in orders_with_location:
            order_items = Item.objects.filter(order=order)
            
            for item in order_items:
                movie = item.movie
                city = order.city or 'Unknown'
                state = order.state or 'Unknown'
                country = order.country or 'Unknown'
                
                trend, created = MovieLocationTrend.objects.get_or_create(
                    movie=movie,
                    city=city,
                    state=state,
                    country=country,
                    date=end_date,
                    defaults={
                        'latitude': order.latitude,
                        'longitude': order.longitude,
                        'purchase_count': item.quantity
                    }
                )
                
                if created:
                    trends_created += 1
                    print(f'Created trend: {movie.name} in {city}, {state} ({item.quantity} purchases)')
                else:
                    if force_regenerate:
                        trend.purchase_count += item.quantity
                        trend.latitude = order.latitude
                        trend.longitude = order.longitude
                        trend.save()
                        trends_updated += 1
                        print(f'Updated trend: {movie.name} in {city}, {state} (total: {trend.purchase_count} purchases)')
                    else:
                        print(f'Skipped existing trend: {movie.name} in {city}, {state}')
        
        print(f'Aggregation complete - Created: {trends_created}, Updated: {trends_updated}')
        
        top_trends = MovieLocationTrend.objects.filter(
            date=end_date
        ).order_by('-purchase_count')[:10]
        
        print('Top trending movies:')
        for trend in top_trends:
            print(f'  {trend.movie.name} - {trend.city}, {trend.state} ({trend.purchase_count} purchases)')
        
        if export_json:
            self.export_for_google_maps(export_file)

    def export_for_google_maps(self, filename):
        print(f'Exporting data to {filename} for Google Maps...')
        
        trends = MovieLocationTrend.objects.all().select_related('movie')
        
        markers = []
        
        for trend in trends:
            marker = {
                'lat': float(trend.latitude),
                'lng': float(trend.longitude),
                'title': f"{trend.movie.name} - {trend.city}, {trend.state}",
                'info': f"<b>{trend.movie.name}</b><br>Location: {trend.city}, {trend.state}<br>Purchases: {trend.purchase_count}<br>Price: ${trend.movie.price}",
                'purchases': trend.purchase_count,
                'movie_name': trend.movie.name,
                'city': trend.city,
                'state': trend.state
            }
            markers.append(marker)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(markers, f, indent=2, ensure_ascii=False)
        
        print(f'Exported {len(markers)} markers to {filename}')