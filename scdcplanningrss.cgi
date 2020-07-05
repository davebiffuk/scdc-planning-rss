#!/usr/bin/perl -w
# vim:ai:cindent:sw=4:ts=4
# https://github.com/davebiffuk/scdc-planning-rss
# Dave Holland <dave@biff.org.uk>

use strict;
use HTML::TreeBuilder;
use HTML::Entities qw(:DEFAULT encode_entities_numeric);
use Getopt::Std;
use CGI qw(:standard);
use LWP::UserAgent;
use WWW::Mechanize;
use DateTime;

our($opt_d, $opt_t, $opt_p, $opt_s);
my ($debug, $parish, $textoutput, $cgi, $te, $ts, $no, $loc,
		$desc, $status, $row, $rfcdate, %paid, $link);
getopts('dtp:'); # debug; text output?; parish
if($opt_d) { $debug=1; }
if($opt_t) { $textoutput=1; }
if($opt_p) { $parish=$opt_p; } else { $parish="Pampisford"; }

my $dtnow = DateTime->now;
my $dtthen = DateTime->now;
$dtthen->subtract(months=>3);

$cgi = CGI->new();
if(param()) {
	if(defined(param('parish'))) {
		$parish=param('parish');
		$parish =~ tr/a-zA-z / /cs;
	}
}

my $mech = WWW::Mechanize->new( autocheck => 1 );
$mech->get('https://applications.greatercambridgeplanning.org/online-applications/search.do?action=advanced');

my ($parishlist) = $mech->find_all_inputs( name => 'searchCriteria.parish' );
my %name_lookup;
@name_lookup{ $parishlist->value_names } = $parishlist->possible_values;
foreach ($parishlist->value_names) {
	next if m/^$/;
	next if m/inactive/i;
	if (m/$parish/i) {
		$mech->select("searchCriteria.parish", $_);
		$debug && print "given '",$parish,"', chose '",$_,"'\n";
		last;
	}
}

$mech->field('date(applicationValidatedStart)', $dtthen->dmy('/') );
$mech->field('date(applicationValidatedEnd)', $dtnow->dmy('/') );

$mech->click_button(value => 'Search');

my $html=$mech->content();

$debug && print "--------------------------------\n";
$debug && print $html."\n\n";
$debug && print "--------------------------------\n";

my $tree = HTML::TreeBuilder->new;
$tree->parse($html);

my $results = $tree->look_down('_tag'=>'ul', 'id'=>'searchresults');
#$results->dump();

my $url="https://applications.greatercambridgeplanning.org/online-applications/search.do?action=simple";
$url=encode_entities($url);

if(!$textoutput) {
	print $cgi->header(-type=>"application/rss+xml");
	print <<EOT;
<?xml version="1.0"?>
<rss version='2.0' xmlns:atom='http://www.w3.org/2005/Atom'>

<channel>
<title>$parish Planning Applications (unofficial)</title>
<link>$url</link>
<description>SCDC Planning Applications for $parish (unofficial)</description>
<generator>planning-to-rss</generator>
EOT
print '<atom:link href="' . $cgi->self_url . '" rel="self" type="application/rss+xml" />', "\n";
}

chomp($rfcdate=`date --rfc-2822`);

foreach my $li ($results->look_down('_tag', 'li')) {
    my $desc = $li->look_down('_tag'=>'a')->as_text;
    my $loc = $li->look_down('_tag'=>'p', 'class'=>'address')->as_text;
    my $no = $li->look_down('_tag'=>'p', 'class'=>'metaInfo')->as_text;
    my $link = $li->look_down('_tag'=>'a')->attr('href');

    $no =~ s/\s*\|.*$//; # the application number is the first field
    $no =~ s/Ref. No://; # remove extra text
	# trim whitespace
	$desc =~ s/^\s+|\s+$//g;
	$loc =~ s/^\s+|\s+$//g;
    $no =~ s/^\s+|\s+$//g;
    $link =~ s/^\s+|\s+$//g;
    $link = "https://applications.greatercambridgeplanning.org" . $link;

	if($textoutput) {
		print $no, "\n  ", $loc, "\n  ", $desc, "\n  ", $link, "\n";
	} else {
		$loc=encode_entities($loc);
		$desc=encode_entities($desc);
		print <<EOT;
<item>
	<title>SCDC planning application $no</title>
	<link>$link</link>
	<guid isPermaLink="false">$no</guid>
	<pubDate>$rfcdate</pubDate>
	<description>&lt;p&gt;$no - $loc&lt;/p&gt;

	&lt;p&gt;$desc&lt;/p&gt;
	</description>
</item>
EOT
		}
	}


if(!$textoutput) {
	print "</channel></rss>\n";
}
