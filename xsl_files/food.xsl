<?xml version="1.0" encoding="UTF-8"?>

<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:fo="http://www.w3.org/1999/XSL/Format">

    <xsl:output method="xml" indent="yes"/>

    <xsl:template match="/">

        <fo:root>

            <fo:layout-master-set>
                <fo:simple-page-master master-name="A4"
                    page-height="29.7cm"
                    page-width="21cm"
                    margin="2cm">

                    <fo:region-body/>
                </fo:simple-page-master>
            </fo:layout-master-set>

            <fo:page-sequence master-reference="A4">
                <fo:flow flow-name="xsl-region-body">

                    <fo:block font-size="18pt"
                              font-weight="bold"
                              space-after="10pt">
                        Breakfast Menu
                    </fo:block>

                    <xsl:for-each select="breakfast_menu/food">

                        <fo:block font-size="14pt"
                                  font-weight="bold"
                                  space-before="8pt">
                            <xsl:value-of select="name"/>
                        </fo:block>

                        <fo:block>
                            Price: <xsl:value-of select="price"/>
                        </fo:block>

                        <fo:block>
                            <xsl:value-of select="description"/>
                        </fo:block>

                        <fo:block space-after="6pt">
                            Calories: <xsl:value-of select="calories"/>
                        </fo:block>

                    </xsl:for-each>

                </fo:flow>
            </fo:page-sequence>

        </fo:root>

    </xsl:template>

</xsl:stylesheet>